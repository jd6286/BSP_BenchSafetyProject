"""
통신을 위한 모듈
"""
import threading
import traceback
import socket
import struct
from queue import Queue

import cv2
import numpy as np


class MessageSender:
    """
    클라이언트로 메시지를 전송하는 클래스

    Args:
        client_socket (socket.socket): 클라이언트 소켓
    """
    def __init__(self, client_socket: socket.socket):
        self._socket = client_socket
    
    def __del__(self):
        self._socket.close()
    
    def send(self, message: str):
        """
        메시지 전송

        Args:
            message (str): 전송할 메시지
        """
        self._socket.sendall(message.encode('utf-8'))


class ImageReceiverThread(threading.Thread):
    """
    이미지 수신 쓰레드

    Args:
        client_socket (socket.socket): 클라이언트 소켓
        image_queue (Queue): 수신한 이미지를 저장할 큐
    """
    def __init__(self, client_socket: socket.socket, image_queue: Queue):
        super().__init__()
        self._socket = client_socket
        self._socket.settimeout(10.0)
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


class ImageDisplayThread(threading.Thread):
    """
    이미지 표시 쓰레드

    Args:
        image_queue (Queue): 이미지가 저장된 큐
    """
    def __init__(self, image_queue: Queue):
        super().__init__()
        self._queue = image_queue
        self._running = True

    def run(self):
        cv2.namedWindow('Press ESC to exit', cv2.WINDOW_NORMAL)

        try:
            while self._running:
                if not self._queue.empty():
                    img = self._queue.get()
                    cv2.imshow('Press ESC to exit', img)
                if cv2.waitKey(1) == 27:
                    break
        except Exception as e:
            traceback.print_exc()
            self._running = False
        finally:
            cv2.destroyAllWindows()
    
    def stop(self):
        self._running = False