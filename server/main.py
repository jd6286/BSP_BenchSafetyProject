"""
서버 메인 파일
"""
from configparser import ConfigParser
from threading import Thread
from queue import Queue

from utils.communication import (
    ImageDisplayThread,
    ImageReceiverThread, 
    MessageSender, 
    create_client_thread)
from utils.model import PersonDetector, PoseClassifier, PoseEstimator


def control_threads(task: str, threads: list[Thread]):
    """
    쓰레드를 제어하는 함수
    """
    if task == 'start':
        for thread in threads:
            thread.daemon = True
            thread.start()
    elif task == 'stop':
        for thread in threads:
            thread.stop()
    elif task == 'join':
        for thread in threads:
            thread.join()


if __name__ == '__main__':
    # Config 파일 읽기
    config = ConfigParser()
    config.read('config.ini')

    client1_image_port = int(config['client1']['img_port'])
    client1_message_port = int(config['client1']['msg_port'])
    # client2_image_port = int(config['client2']['img_port'])
    # client2_message_port = int(config['client2']['msg_port'])

    # 연결 정보
    server_ip = '0.0.0.0'
    ports = [
        (client1_image_port, 'Client1 Image'), 
        (client1_message_port, 'Client1 Message'), 
        # (client2_image_port, 'Client2 Image'), 
        # (client2_message_port, 'Client2 Message')
    ]

    # 통신 쓰레드 생성
    client_threads = {}
    create_client_thread(server_ip, ports, client_threads)
    
    client1_image_queue, client1_image_thread, client1_display_thread = client_threads['Client1 Image']
    client1_message_sender = client_threads['Client1 Message']
    # client2_image_queue, client2_image_thread, client2_display_thread = client_sockets['Client2 Image']
    # client2_message_sender = client_sockets['Client2 Message']

    thread_list = [
        client1_image_thread, 
        client1_display_thread, 
        # client2_image_thread, 
        # client2_display_thread
    ]

    # 쓰레드 시작
    control_threads('start', thread_list)

    try:
        while True:
            pass
    except Exception as e:
        print(e)
    finally:
        control_threads('stop', thread_list)

    # 쓰레드 종료 대기
    control_threads('join', thread_list)
