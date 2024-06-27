"""
자세 추론 모듈
"""
import configparser
import time
from collections import deque

import cv2
import numpy as np

from utils.model import PersonDetector, PoseClassifier, PoseEstimator


# 설정 가져오기
__config = configparser.ConfigParser()
__config.read('config.ini')

PERSON_DETECTION_MODEL_PATH = __config['model']['person_detection']
POSE_ESTIMATION_MODEL_PATH = __config['model']['pose_estimation']
POSE_CLASSIFICATION_MODEL_PATH = __config['model']['pose_classification']

POSE_THRESHOLD = float(__config['inference']['pose_threshold'])
PULL_STATE_DURATION = int(__config['inference']['pull_state_duration'])
INITIAL_FRAME_IGNORE = int(__config['inference']['initial_frame_ignore'])
DETECTION_FRAME_THRESHOLD = int(__config['inference']['detection_frame_threshold'])
HISTORY_LENGTH = int(__config['inference']['history_length'])


class InferenceState:
    """
    추론 상태를 관리하는 클래스
    """
    def __init__(self):
        self.selected_index = 2  # 마지막으로 선택된 상태(0: pull, 1: push, 2: unknown)
        self.result_history = deque(maxlen=HISTORY_LENGTH)  # 최근 N개의 결과를 저장할 deque
        self.conf_history = deque(maxlen=HISTORY_LENGTH)  # 최근 N개의 신뢰도를 저장할 deque
        self.pull_start_time = None  # 'pull' 상태가 시작된 시간을 기록
        self.warning_active = False  # 경고 상태 여부
        self.last_warning_time = None  # 마지막으로 메시지를 보낸 시간
        self.person_detected_frame_count = 0  # 사람이 감지된 프레임 수
        self.low_confidence_count = 0  # 신뢰도가 낮은 프레임 수
        self.person_detected = False  # 사람이 감지되었는지 여부
    
    def reset_state(self):
        """
        상태 초기화
        """
        self.warning_active = False
        self.person_detected_frame_count = 0
        self.pull_start_time = None
        self.result_history.clear()
        self.conf_history.clear()
        self.selected_index = 2


class Inferencer:
    """
    자세 추론을 위한 클래스
    """
    def __init__(self):
        self.person_detector = PersonDetector(PERSON_DETECTION_MODEL_PATH)
        self.pose_estimator = PoseEstimator(POSE_ESTIMATION_MODEL_PATH)
        self.pose_classifier = PoseClassifier(POSE_CLASSIFICATION_MODEL_PATH)

        self.on_set_warning = self._default_callback
        self.on_reset_warning = self._default_callback
    
    def _default_callback(self):
        pass

    def inference(self, frame: np.ndarray, state: InferenceState):
        """
        입력된 이미지를 추론하는 함수

        Args:
            frame (numpy.ndarray): 비디오 프레임
            state (InferenceState): 상태를 관리하는 객체
        """
        # 사람 감지
        boxes, scores, labels = self.person_detector.predict(frame)
        state.person_detected = len(boxes) > 0

        # 사람이 감지되면
        if state.person_detected:
            state.person_detected_frame_count += 1
            # detection_frame_threshold만큼 프레임 소모 후 포즈 측정 활성화
            if state.person_detected_frame_count > DETECTION_FRAME_THRESHOLD:
                self._inference_pose(frame, boxes, state)

        # 사람이 감지되지 않으면 변수 초기화
        else:
            if state.warning_active:
                self.on_reset_warning()
            state.reset_state() 

    def _crop_roi(self, frame: np.ndarray, boxes: np.ndarray, padding: int = 0):
        """
        사람 영역만 크롭하는 함수
        
        Args:
            frame (numpy.ndarray): 비디오 프레임
            boxes (list): 감지된 객체의 경계 상자 리스트
            padding (int, optional): 경계 상자에 추가할 여백

        Returns:
            numpy.ndarray: 크롭된 ROI(관심 영역)
        """
        height, width, _ = frame.shape
        x1, y1, x2, y2 = list(map(int, boxes[0]))
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)
        roi = frame[y1:y2, x1:x2]
        return roi
    
    def _inference_pose(self, frame: np.ndarray, boxes: np.ndarray, state: InferenceState):
        """
        포즈를 처리하는 내부 함수

        Args:
            frame (numpy.ndarray): 비디오 프레임
            boxes (list): 감지된 객체의 경계 상자 리스트
            state (InferenceState): 상태를 관리하는 객체
        """
        # 관심 영역(ROI) 크롭
        roi = self._crop_roi(frame, boxes, 10)

        # ROI내에서 포즈 추정 이미지 추출
        skeleton_image = self.pose_estimator.predict(roi)

        # 추출한 포즈 추정 이미지로 포즈 분류
        predicted_index, confidence = self.pose_classifier.predict(skeleton_image)

        # 결과의 신뢰도가 pose_threshold를 넘은 경우
        if confidence > POSE_THRESHOLD:
            # 결과와 신뢰도를 기록
            state.result_history.append(predicted_index)
            state.conf_history.append(confidence)

            # result_history.maxlen 주기로 중간값 필터링
            if len(state.result_history) == state.result_history.maxlen:
                state.selected_index = int(np.median(state.result_history))

            # pull동작인 경우 _handle_pull_state활성화
            if state.selected_index == 0:
                self._handle_pull_state(state)
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

    def _handle_pull_state(self, state: InferenceState):
        """
        'pull' 상태를 처리하는 내부 함수

        Args:
            state (InferenceState): 상태를 관리하는 객체
        """
        if state.pull_start_time is None:
            state.pull_start_time = time.time()

        elapsed_time = time.time() - state.pull_start_time
        # pull_state_duration만큼의 시간동안 pull상태가 지속되는 경우
        if elapsed_time > PULL_STATE_DURATION:
            if not state.warning_active:
                self.on_set_warning()
            state.warning_active = True # warning 활성화
            state.pull_start_time = None
