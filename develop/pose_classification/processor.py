import time
import numpy as np
from collections import deque
from utils.model import PersonDetector, PoseEstimator, PoseClassifier
from utils.utils import crop_roi
import config

class ProcessState:
    """
    상태를 관리하는 클래스
    """
    def __init__(self):
        """ㄴ
        초기화 함수
        """
        self.selected_index = 2  # 초기 상태 (unknown)
        self.result_history = deque(maxlen=config.HISTORY_LENGTH)  # 최근 N개의 결과를 저장할 deque
        self.conf_history = deque(maxlen=config.HISTORY_LENGTH)  # 최근 N개의 신뢰도를 저장할 deque
        self.pull_start_time = None  # 'pull' 상태가 시작된 시간을 기록
        self.warning_active = False  # 경고 상태 여부
        self.last_warning_time = None  # 마지막으로 메시지를 보낸 시간
        self.person_detected_frame_count = 0  # 사람이 감지된 프레임 수
        self.detection_frame_threshold = config.DETECTION_FRAME_THRESHOLD  # 포즈 측정을 활성화하기 위해 필요한 프레임 수
        self.pose_threshold = config.POSE_THRESHOLD  # 포즈 분류 신뢰도 임계값
        self.pull_state_duration = config.PULL_STATE_DURATION  # 'pull' 상태가 유지되는 시간
        self.low_confidence_count = 0  # 신뢰도가 낮은 프레임 수
        self.person_detected = False  # 사람이 감지되었는지 여부


class PoseProcessor:
    """
    포즈 처리기 클래스
    """
    def __init__(self):
        """
        포즈 처리기 초기화 함수
        """
        self.person_detector = PersonDetector(model_path=config.PERSON_DETECTION_MODEL_PATH, device=config.DEVICE)
        self.pose_estimator = PoseEstimator(model_path=config.POSE_ESTIMATION_MODEL_PATH, device=config.DEVICE)
        self.pose_classifier = PoseClassifier(model_path=config.POSE_CLASSIFICATION_MODEL_PATH, device=config.DEVICE)

    def process_frame(self, frame, state):
        """
        비디오 프레임을 처리하는 함수

        Args:
            frame (numpy.ndarray): 비디오 프레임
            state (ProcessState): 상태를 관리하는 객체
        """
        # 사람 감지
        boxes, scores, labels = self.person_detector.predict(frame)
        state.person_detected = len(boxes) > 0

        # 사람이 감지되면
        if state.person_detected:
            state.person_detected_frame_count += 1
            # detection_frame_threshold만큼 프레임 소모 후 포즈 측정 활성화
            if state.person_detected_frame_count > state.detection_frame_threshold:
                self._process_pose(frame, boxes, state)
        # 사람이 감지되지 않으면 변수 초기화
        else:
            self._reset_state(state)
    
    def _process_pose(self, frame, boxes, state):
        """
        포즈를 처리하는 내부 함수

        Args:
            frame (numpy.ndarray): 비디오 프레임
            boxes (list): 감지된 객체의 경계 상자 리스트
            state (ProcessState): 상태를 관리하는 객체
        """
        # 관심 영역(ROI) 크롭
        roi = crop_roi(frame, boxes, 10)

        # ROI내에서 포즈 추정 이미지 추출
        skeleton_image = self.pose_estimator.predict(roi)

        # 추출한 포즈 추정 이미지로 포즈 분류
        predicted_index, confidence = self.pose_classifier.predict(skeleton_image)

        # 결과의 신뢰도가 pose_threshold를 넘은 경우
        if confidence > state.pose_threshold:
            # 결과와 신뢰도를 기록
            state.result_history.append(predicted_index)
            state.conf_history.append(confidence)
            # result_history.maxlen 주기로 중간값 필터링
            if len(state.result_history) == state.result_history.maxlen:
                state.selected_index = int(np.median(state.result_history))
            # pull동작인 경우 _handle_pull_state활성화
            if state.selected_index == 0:
                self._handle_pull_state(frame, state)
            # 그 외의 동작은 pull동작 변수 초기화
            else:
                state.pull_start_time = None
            # 신뢰도 낮은 프레임 수 초기화
            state.low_confidence_count = 0  
        # 신뢰도가 pose_threshold보다 낮은 경우
        else:
            state.low_confidence_count += 1
            # 연속으로 5번 낮은 결과가 나오면 unknown 상태
            if state.low_confidence_count >= 5:
                state.selected_index = 2  # unknown
                state.low_confidence_count = 0

    def _handle_pull_state(self, frame, state):
        """
        'pull' 상태를 처리하는 내부 함수

        Args:
            frame (numpy.ndarray): 비디오 프레임
            state (ProcessState): 상태를 관리하는 객체
        """
        if state.pull_start_time is None:
            state.pull_start_time = time.time()
        elapsed_time = time.time() - state.pull_start_time
        # pull_state_duration만큼의 시간동안 pull상태가 지속되는 경우
        if elapsed_time > state.pull_state_duration:
            state.warning_active = True # warning 활성화
            state.pull_start_time = None

    def _reset_state(self, state):
        """
        상태를 초기화하는 내부 함수

        Args:
            state (ProcessState): 상태를 관리하는 객체
        """
        state.warning_active = False
        state.person_detected_frame_count = 0
        state.pull_start_time = None
        state.result_history.clear()
        state.conf_history.clear()
        state.selected_index = 2
