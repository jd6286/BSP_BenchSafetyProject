"""
서버 메인 파일
"""
from queue import Queue

from utils.communication import MessageSender, init_communication
from utils.inference import Inferencer
from utils.thread import ImageReceiveThread


if __name__ == '__main__':
    # 클라이언트와의 통신 초기화
    thread_dict = {}
    init_communication(thread_dict)

    # 쓰레드 객체
    client1_image_receiver: ImageReceiveThread = thread_dict['Client1 Image'][0]
    client1_receive_queue: Queue = thread_dict['Client1 Image'][1]
    client1_message_sender: MessageSender = thread_dict['Client1 Message']

    # 쓰레드 시작
    client1_image_receiver.start()

    # 무한 루프
    try:
        while True:
            pass
    except Exception as e:
        print(e)
    finally:
        client1_image_receiver.stop()

    client1_image_receiver.join()

