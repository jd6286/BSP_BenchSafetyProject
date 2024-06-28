"""
서버 메인 파일
"""
import tkinter as tk
import traceback
from queue import Queue

import cv2

from utils.communication import MessageSender, init_communication, remote_start
from utils.inference import Inferencer, InferenceState
from utils.thread import ImageReceiveThread, MessageReceiveThread


# 프로세스 실행 여부
running = True
popup_state = False


def show_warning_popup(message):
    """
    경고 팝업 창 표시
    """
    global popup_state

    if popup_state:
        return

    def blink():
        current_color = root.cget("background")
        next_color = "red" if current_color == "white" else "white"
        root.configure(background=next_color)
        root.after(500, blink)  # 500ms마다 색상 변경

    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨기기
    root.deiconify()  # 숨기기 취소
    root.title("경고")
    root.geometry("800x600")
    root.configure(background="white")

    label = tk.Label(root, text=message, font=("Helvetica", 30))
    label.pack(expand=True)
    popup_state = True

    blink()
    root.mainloop()

def set_warning_handler():
    client1_message_sender.send('buzzer on')
    show_warning_popup("Warning on Bench Press Zone!")


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
    client2_message_receiver.start()

    # 추론 객체 생성
    pose_class = ['pull', 'push', 'unknown']
    inferencer = Inferencer()
    state = InferenceState()

    inferencer.on_set_warning = lambda: set_warning_handler()
    inferencer.on_reset_warning = lambda: client1_message_sender.send('buzzer off')
    client2_message_receiver.add_callback(
        "Warning on Bench Press Zone!", 
        lambda: show_warning_popup("Warning on Bench Press Zone!"))

    # 무한 루프
    try:
        # Client1 이미지 추론
        while running:
            if not client1_receive_queue.empty():
                frame = client1_receive_queue.get()
                inferencer.inference(frame, state)
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
