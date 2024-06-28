## 라즈베리와의 서버 통신 / 라즈베리파이에서 데이터를 수신 받아 경고창을 띄움

import socket
import tkinter as tk


# 팝업 창 함수 정의
def show_warning_popup(message):
    def blink():
        current_color = root.cget("background")
        next_color = "red" if current_color == "white" else "white"
        root.configure(background=next_color)
        root.after(500, blink)  # 500ms마다 색상 변경

    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨기기q
    root.deiconify()  # 숨기기 취소
    root.title("경고")
    root.geometry("800x600")
    root.configure(background="white")

    label = tk.Label(root, text=message, font=("Helvetica", 30))
    label.pack(expand=True)

    blink()
    root.mainloop()

# 서버의 IP 주소와 포트 번호
SERVER_IP = '0.0.0.0'  # 모든 인터페이스에서 연결을 수신하려면 0.0.0.0
SERVER_PORT = 22222  # 클라이언트와 동일한 포트 번호

# 서버 소켓 생성
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 소켓을 특정 주소와 포트에 바인딩
server_socket.bind((SERVER_IP, SERVER_PORT))

# 클라이언트 연결을 수신할 준비
server_socket.listen(1)  # 최대 1개의 클라이언트 연결을 수신

print(f"서버가 {SERVER_IP}:{SERVER_PORT}에서 실행 중입니다.")

# 클라이언트 연결을 수락하고 데이터를 수신
client_socket, client_address = server_socket.accept()
print(f"{client_address}에서 연결됨")

while True:
    # 클라이언트로부터 데이터 수신
    data = client_socket.recv(1024)
    if not data:
        break
    
    # 수신한 데이터 디코딩
    message = data.decode('utf-8')
    print(message)
    
    # 특정 메시지를 수신하면 팝업창 띄우기
    if message == "Warning on Bench Press Zone!":
        show_warning_popup(message)

# 연결 종료
client_socket.close()
server_socket.close()