import cv2
import config
import logging

def draw_box(frame, boxes, padding=0):
    """
    Object Detection 결과를 사각형으로 그려주는 함수 (디버깅 용)
    
    Args:
        frame (numpy.ndarray): 비디오 프레임
        boxes (list): 감지된 객체의 경계 상자 리스트
        padding (int, optional): 경계 상자에 추가할 여백

    Returns:
        numpy.ndarray: 경계 상자가 그려진 비디오 프레임
    """
    height, width, _ = frame.shape
    for box in boxes:
        x1, y1, x2, y2 = list(map(int, box))
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)
        cv2.rectangle(frame, (x1, y1), (x2, y2), config.BBOX_COLOR, 2)
    return frame


def crop_roi(frame, boxes, padding=0):
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


def display_frame_info(frame, state, frame_count, class_name):
    """
    분류 정보를 출력하는 함수
    
    Args:
        frame (numpy.ndarray): 비디오 프레임
        boxes (list): 감지된 객체의 경계 상자 리스트
        frame_count: 현재 프레임 카운트
        class_name: 분류명
    """
    if state.person_detected:
        if state.warning_active:
            cv2.putText(frame, 'warning', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            logging.warning('Pull state warning')
        else:
            if frame_count <= config.INITIAL_FRAME_IGNORE:
                cv2.putText(frame, 'initializing...', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, config.EXCEPTION_COLOR, 2)
                logging.info(f'{class_name[state.selected_index]}: {state.conf_history[-1] if state.conf_history else "N/A"}')
            else:
                cv2.putText(frame, class_name[state.selected_index], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, config.NORMAL_COLOR, 2)
                logging.info(f'{class_name[state.selected_index]}: {state.conf_history[-1] if state.conf_history else "N/A"}')
    else:
        cv2.putText(frame, 'no person detected', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, config.EXCEPTION_COLOR, 2)
        logging.info('no person detected')