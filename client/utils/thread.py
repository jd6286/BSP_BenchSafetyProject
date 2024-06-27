import socket
import struct
import threading
import traceback

import cv2


class ImageSendThread(threading.Thread):
    """
    서버로 이미지를 전송하는 쓰레드

    Args:
        image_socket (socket.socket): 이미지 송신용 소켓
    """
    def __init__(self, image_socket: socket.socket):
        super().__init__()
        self._socket = image_socket             # 이미지 송신용 소켓
        self._camera = cv2.VideoCapture(0)      # 웹캠
        self._running = True                    # 쓰레드 실행 여부

        if not self._camera.isOpened():
            print('Error: Could not open webcam.')
    
    def __del__(self):
        self._socket.close()
        if self._camera is not None:
            self._camera.release()

    def run(self):
        try:
            while self._running:
                # 웹캠에서 이미지를 읽어옴
                ret, frame = self._camera.read()
                if not ret:
                    print('Error: Could not read frame from webcam.')
                    break

                # 이미지를 JPEG 포맷으로 인코딩 후 바이트로 변환
                _, img_encoded = cv2.imencode('.jpg', frame)
                img_bytes = img_encoded.tobytes()
                img_size = len(img_bytes)

                # 이미지 크기를 네트워크 바이트 오더로 변환하여 전송
                self._socket.sendall(struct.pack(">L", img_size) + img_bytes)
        except Exception as e:
            traceback.print_exc()
            self._running = False
    
    def stop(self):
        self._running = False


class MessageReceiveThread(threading.Thread):
    """
    서버로부터 메시지를 수신하는 쓰레드

    Args:
        message_socket (socket.socket): 메시지 수신용 소켓
    """
    def __init__(self, message_socket: socket.socket):
        super().__init__()
        self._socket = message_socket           # 메시지 수신용 소켓
        self._running = True                    # 쓰레드 실행 여부
        self._on_message_received = self._default_callback  # 메시지 수신 시 호출할 콜백 함수
    
    def __del__(self):
        self._socket.close()
    
    @property
    def on_message_received(self):
        return self._on_message_received
    
    @on_message_received.setter
    def on_message_received(self, callback):
        self._on_message_received = callback

    def _default_callback(self, message: str):
        """
        메시지 수신 시 호출할 기본 콜백 함수

        Args:
            message (str): 수신한 메시지
        """
        print(f'Message from the server: {message}')

    def run(self):
        try:
            while self._running:
                # 메시지 수신
                message = self._socket.recv(1024).decode('utf-8')
                if not message:
                    break

                # 수신한 메시지를 콜백 함수에 전달
                self._on_message_received(message)   
        except Exception as e:
            traceback.print_exc()
            self._running = False
    
    def stop(self):
        self._running = False