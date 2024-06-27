"""
쓰레드 모듈
"""
import socket
import struct
import traceback
import threading
from queue import Queue

import cv2
import numpy as np

from utils.model import PersonDetector, PoseClassifier, PoseEstimator


class ImageReceiveThread(threading.Thread):
    """
    이미지 수신 쓰레드

    Args:
        client_socket (socket.socket): 클라이언트 소켓
        image_queue (Queue): 수신한 이미지를 저장할 큐
    """
    def __init__(self, client_socket: socket.socket, image_queue: Queue):
        super().__init__()
        self._socket = client_socket
        self._queue = image_queue
        self._running = True
    
    def __del__(self):
        self._socket.close()
        cv2.destroyAllWindows()
    
    def run(self):
        # 이미지 수신
        try:
            while self._running:
                # 이미지 크기 수신
                img_size_data = self._socket.recv(4)
                if not img_size_data:
                    break
                img_size = struct.unpack(">L", img_size_data)[0]

                # 이미지 데이터 수신
                img_data = b""
                while len(img_data) < img_size:
                    data = self._socket.recv(img_size - len(img_data))
                    if not data:
                        break
                    img_data += data
                
                # 수신한 데이터를 이미지로 변환하여 큐에 추가
                img_array = np.frombuffer(img_data, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                self._queue.put(img)
        except Exception as e:
            traceback.print_exc()
            self._running = False

    def stop(self):
        self._running = False


class InferenceThread(threading.Thread):
    """
    자세 추론 쓰레드

    Args:
        image_queue (Queue): 이미지가 저장된 큐
    """
    pose_class = ['pull', 'push', 'unknown']
    POSE_THRESHOLD = 0.7

    def __init__(self, image_queue: Queue):
        super().__init__()
        self._queue = image_queue
        self._running = True

        self._person_detector = PersonDetector('models/person-detection-0202.xml')
        self._pose_estimator = PoseEstimator('models/singlepose-thunder-tflite-float16.xml')
        self._pose_classifier = PoseClassifier('models/pose-classification-03.xml')

        self.last_pose = self.pose_class[2]
    
    def _crop_roi(self, frame, boxes, padding=0):
        """
        사람 영역만 크롭하는 함수

        Args:
            frame (np.ndarray): 원본 이미지
            boxes (np.ndarray): Object Detection 결과
            padding (int): 크롭 시 패딩 값
        """
        height, width, _ = frame.shape

        x1, y1, x2, y2 = list(map(int, boxes[0]))
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)

        roi = frame[y1:y2, x1:x2]
        
        return roi
    
    def _do_inference(self, frame: np.ndarray):
        """
        추론 수행 함수
        """
        # Person Detection
        boxes, _, _ = self._person_detector.predict(frame)
        if len(boxes) == 0:
            return frame
            # return 'No Person Detected'
        
        # Pose Estimation
        roi = self._crop_roi(frame, boxes)
        skeleton_img = self._pose_estimator.predict(roi)

        # Pose Classification
        idx, conf = self._pose_classifier.predict(skeleton_img)
        color = (0, 255, 0) if conf > self.POSE_THRESHOLD else (0, 0, 255)
        if conf > self.POSE_THRESHOLD:
            self.last_pose = self.pose_class[idx]
        cv2.putText(frame, self.last_pose, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        return frame
        # return self.last_pose

    def run(self):
        cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)

        try:
            while self._running:
                if not self._queue.empty():
                    frame = self._queue.get()
                    image = self._do_inference(frame)
                    cv2.imshow('Frame', image)
        except Exception as e:
            traceback.print_exc()
            self._running = False
        finally:
            cv2.destroyAllWindows()
    
    def stop(self):
        self._running = False
