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

from utils.thread import ImageReceiveThread, ImageDisplayThread


# 설정 가져오기
config = configparser.ConfigParser()
config.read('config.ini')

SERVER_IP = '0.0.0.0'

CLIENT1_IP = config['client1']['ip']
CLIENT1_REMOTE_PORT = int(config['client1']['remote_port'])
CLIENT1_IMAGE_PORT = int(config['client1']['img_port'])
CLIENT1_MESSAGE_PORT = int(config['client1']['msg_port'])


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


def remote_start():
    """
    클라이언트를 원격 실행하는 함수
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((CLIENT1_IP, CLIENT1_REMOTE_PORT))
    server_socket.sendall('start'.encode('utf-8'))
    server_socket.close()

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
        receive_queue = Queue()
        image_receive_thread = ImageReceiveThread(client_socket, receive_queue)
        return_dict[key] = (image_receive_thread, receive_queue)
    elif 'Message' in key:
        return_dict[key] = MessageSender(client_socket)
    else:
        raise ValueError(f'Invalid key: {key}')


def init_communication(return_dict: dict):
    """
    통신 초기화 함수
    """   
    ports = [
        (CLIENT1_IMAGE_PORT, 'Client1 Image'), 
        (CLIENT1_MESSAGE_PORT, 'Client1 Message')
    ]

    # 통신 쓰레드 생성
    temp_threads = []
    for port, key in ports:
        # 서버 소켓 생성
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_IP, port))

        # 클라이언트 연결 대기
        server_socket.listen()
        print(f'Waiting for a client to connect on {SERVER_IP}:{port}... ({key})')
        thread = threading.Thread(target=accept_connection, 
                                  args=(server_socket, key, return_dict))
        thread.daemon = True
        thread.start()
        temp_threads.append(thread)
    
    for thread in temp_threads:
        thread.join()
