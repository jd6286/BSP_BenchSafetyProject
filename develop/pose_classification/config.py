# 모델 설정
PERSON_DETECTION_MODEL_PATH = 'models/person-detection-0202.xml'
POSE_ESTIMATION_MODEL_PATH = 'models/singlepose-thunder-tflite-float16.xml'
POSE_CLASSIFICATION_MODEL_PATH = 'models/pose_classification_03.xml'
DEVICE = 'CPU'  # 사용할 디바이스 ('CPU', 'GPU' 등)

# 임계값 설정
POSE_THRESHOLD = 0.7

# 경고 조건 설정
PULL_STATE_DURATION = 10  # 'pull' 상태가 유지되는 시간 (초)

# 프레임 설정
INITIAL_FRAME_IGNORE = 60  # 초기 몇 프레임을 무시할지 설정
DETECTION_FRAME_THRESHOLD = 60  # 포즈 측정을 활성화하기 위해 필요한 프레임 수

# 버퍼 크기 설정
HISTORY_LENGTH = 10  # 결과 히스토리 및 신뢰도 히스토리의 버퍼 크기

# 디버깅 설정
BBOX_COLOR = (0, 255, 0)  # 경계 상자 색상 (BGR)
NORMAL_COLOR = (0, 255, 0) # 일반 상황 텍스트
EXCEPTION_COLOR = (0, 0, 255) # 예외 상황 텍스트