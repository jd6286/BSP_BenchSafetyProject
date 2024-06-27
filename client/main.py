"""
클라이언트 메인 파일
"""
from utils.communication import init_communication
from utils.thread import ImageSendThread, MessageReceiveThread


# 통신 종료 함수
def stop_communication(image_sender: ImageSendThread, 
                       message_receiver: MessageReceiveThread):
    """
    통신 종료 함수

    Args:
        image_sender (ImageSendThread): 이미지 송신 쓰레드
        message_receiver (MessageReceiveThread): 메시지 수신 쓰레드
    """
    if image_sender is not None and image_sender.is_alive():
        image_sender.stop()
    if message_receiver is not None and message_receiver.is_alive():
        message_receiver.stop()


if __name__ == "__main__":
    # 통신 초기화
    threads = init_communication()
    image_sender: ImageSendThread = threads[0]
    message_receiver: MessageReceiveThread = threads[1]

    # 메시지 콜백 등록
    message_receiver.add_callback('exit', lambda: stop_communication(image_sender, message_receiver))

    try:
        while True:
            pass
    except Exception as e:
        print(e)
    finally:
        stop_communication(image_sender, message_receiver)
