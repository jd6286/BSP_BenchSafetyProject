"""
통신을 위한 모듈
"""
import sys
import configparser
import socket
import traceback

from utils.thread import ImageSendThread, MessageReceiveThread


def init_communication():
    """
    통신 초기화 함수

    Returns:
        ImageSendThread: 이미지 송신 쓰레드
        MessageReceiveThread: 메시지 수신 쓰레드
    """
    # Config 파일 읽기
    config = configparser.ConfigParser()
    config.read('config.ini')

    # 서버 IP, 포트 설정
    server_ip = config['server']['ip']
    image_port =  int(config['server']['img_port'])
    message_port = int(config['server']['msg_port'])

    # 소켓 생성
    image_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    message_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 서버에 연결
    try:
        print(f'Connecting to the server {server_ip}:{image_port}...')
        image_socket.connect((server_ip, image_port))
        print(f'Connecting to the server {server_ip}:{message_port}...')
        message_socket.connect((server_ip, message_port))
        print('Connected to the server.')
    except ConnectionRefusedError:
        print('Connection is refused by the server.')
        return
    except Exception:
        traceback.print_exc()
        return
    
    # 쓰레드 실행
    image_send_thread = ImageSendThread(image_socket)
    image_send_thread.daemon = True
    image_send_thread.start()

    message_receive_thread = MessageReceiveThread(message_socket)
    message_receive_thread.daemon = True
    message_receive_thread.start()

    return image_send_thread, message_receive_thread
