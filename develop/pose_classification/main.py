import sys
import argparse
import os
import cv2
import logging
from processor import ProcessState, PoseProcessor
from utils.utils import display_frame_info


def main(source):
    """
    메인 함수

    Args:
        source (str): 비디오 소스 경로
    """
    class_name = ['pull', 'push', 'unknown']    # 분류명
    pose_processor = PoseProcessor()    # 포즈 처리 클래스
    state = ProcessState()  # 프로세스 상태 초기화 

    if not os.path.exists(source):
        logging.error(f'File not found: {source}')
        sys.exit(1)
    
    # cv2 영상 이미지 캡처
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logging.error(f'Error opening video source: {source}')
        sys.exit(1)

    current_frame_count = 0  # 현재 프레임 수 초기화

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 프레임 처리
            pose_processor.process_frame(frame, state)
            current_frame_count += 1  # 현재 프레임 수 증가

            display_frame_info(frame, state, current_frame_count, class_name)
            cv2.imshow('Press ESC to exit', frame)

            if cv2.waitKey(1) == 27:
                break

    except Exception as e:
        logging.error(f'Error during processing: {e}')
    finally:
        #client_socket.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s', type=str, help='Input source', required=True)
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, 'INFO'))
    main(args.source)
