"""
서버 메인 파일
"""
import traceback
from queue import Queue

import cv2

from utils.communication import MessageSender, init_communication, remote_start
from utils.inference import Inferencer, InferenceState
from utils.thread import ImageReceiveThread, MessageReceiveThread


# 프로세스 실행 여부
running = True


def exit_process():
    """
    프로세스 종료
    """
    global running

    cv2.destroyAllWindows()
    client2_message_receiver.stop()
    client1_image_receiver.stop()
    client1_message_sender.send('buzzer off')
    client1_message_sender.send('exit')
    running = False


if __name__ == '__main__':
    # 클라이언트와의 통신 초기화
    remote_start()

    thread_dict = {}
    init_communication(thread_dict)

    # 쓰레드 객체
    client1_image_receiver: ImageReceiveThread = thread_dict['Client1 Image'][0]
    client1_receive_queue: Queue = thread_dict['Client1 Image'][1]
    client1_message_sender: MessageSender = thread_dict['Client1 Message']
    client2_message_receiver: MessageReceiveThread = thread_dict['Client2 Message']

    # 쓰레드 시작
    client1_image_receiver.start()
    # client2_message_receiver.start()

    # 추론 객체 생성
    pose_class = ['pull', 'push', 'unknown']
    inferencer = Inferencer()
    state = InferenceState()

    inferencer.on_set_warning = lambda: client1_message_sender.send('buzzer on')
    inferencer.on_reset_warning = lambda: client1_message_sender.send('buzzer off')

    # 무한 루프
    try:
        # Client1 이미지 추론
        while running:
            if not client1_receive_queue.empty():
                frame = client1_receive_queue.get()
                inferencer.inference(frame, state)
                print(pose_class[state.selected_index], f'warning:{state.warning_active}')
                cv2.imshow('frame', frame)
                cv2.waitKey(1)
            if not client1_image_receiver.is_alive():
                break
    except KeyboardInterrupt:
        exit_process()
        print('Program is terminated by the user.')
    except Exception as e:
        traceback.print_exc()
    finally:
        if running:
            exit_process()
