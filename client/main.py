"""
클라이언트 메인 파일
"""
from utils.communication import init_communication
from utils.thread import ImageSendThread, MessageReceiveThread


if __name__ == "__main__":
    threads = init_communication()
    image_send_thread: ImageSendThread = threads[0]
    message_receive_thread: MessageReceiveThread = threads[1]

    try:
        while True:
            pass
    except Exception as e:
        print(e)
    finally:
        image_send_thread.stop()
        message_receive_thread.stop()

    image_send_thread.join()
    message_receive_thread.join()
