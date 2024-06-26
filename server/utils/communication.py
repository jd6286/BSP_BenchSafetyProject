"""
통신을 위한 모듈
"""
if __name__ == '__main__':
    import sys
    print('This script cannot be run independently.')
    sys.exit(1)

import configparser
import threading
import socket
from typing import Any
from queue import Queue

from utils.thread import ImageReceiveThread, InferenceThread


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


def accept_connection(
        server_socket: socket.socket, 
        key: str, 
        return_dict: dict[str, Any]):
    """
    클라이언트와 연결하는 함수

    Args:
        server_socket (socket.socket): 서버 소켓
        key (str): 딕셔너리 키
        return_dict (dict): 쓰레드 객체를 저장할 딕셔너리
    """
    # 클라이언트 연결
    client_socket, addr = server_socket.accept()
    print(f'Connected to a client {addr}. ({key})')

    # Key에 맞는 객체 생성 후 딕셔너리에 저장
    if 'Image' in key:
        image_queue = Queue()
        image_receive_thread = ImageReceiveThread(client_socket, image_queue)
        inference_thread = InferenceThread(image_queue)
        return_dict[key] = (image_receive_thread, inference_thread)
    elif 'Message' in key:
        return_dict[key] = MessageSender(client_socket)
    else:
        raise ValueError(f'Invalid key: {key}')


def init_communication(return_dict: dict):
    """
    통신 초기화 함수
    """
    # Config 파일 읽기
    config = configparser.ConfigParser()
    config.read('config.ini')

    # 연결 정보
    server_ip = '0.0.0.0'
    client1_image_port = int(config['client1']['img_port'])
    client1_message_port = int(config['client1']['msg_port'])
    # client2_image_port = int(config['client2']['img_port'])
    # client2_message_port = int(config['client2']['msg_port'])
    
    ports = [
        (client1_image_port, 'Client1 Image'), 
        (client1_message_port, 'Client1 Message'), 
        # (client2_image_port, 'Client2 Image'), 
        # (client2_message_port, 'Client2 Message')
    ]

    # 통신 쓰레드 생성
    temp_threads = []
    for port, key in ports:
        # 서버 소켓 생성
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((server_ip, port))

        # 클라이언트 연결 대기
        server_socket.listen()
        print(f'Waiting for a client to connect on {server_ip}:{port}... ({key})')
        thread = threading.Thread(target=accept_connection, 
                                  args=(server_socket, key, return_dict))
        thread.daemon = True
        thread.start()
        temp_threads.append(thread)
    
    for thread in temp_threads:
        thread.join()

    # 쓰레드 실행
    for key, threads in return_dict.items():
        if 'Image' in key:
            for thread in threads:
                thread.daemon = True
                thread.start()
        elif 'Message' in key:
            pass
        else:
            raise ValueError(f'Invalid key: {key}')