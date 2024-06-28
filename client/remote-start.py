"""
서버로부터 프로그램 원격 실행 명령을 대기하는 프로그램
"""
import configparser
import socket
import subprocess
import time


# 클라이언트 디렉토리
CLIENT_DIR = "/home/pi/openvino-project/client/"


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(CLIENT_DIR + "config.ini")

    client_ip = '0.0.0.0'
    remote_port = int(config["server"]["remote_port"])
    
    while True:
        # 클라이언트 소켓 생성
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.bind((client_ip, remote_port))

        client_socket.listen(1)
        print(f'Listening on {client_ip}:{remote_port} for remote start...')

        # 서버와 연결
        server_socket, addr = client_socket.accept()
        print("Connected by", addr)

        # 서버로부터 명령 수신
        data = server_socket.recv(1024).decode('utf-8')
        if data == "start":
            # 프로그램 실행
            print("Starting program...")
            time.sleep(3)
            subprocess.run(["/bin/bash", CLIENT_DIR + "remote-start.sh"])
        else:
            print("Invalid command:", data)
        
        # 소켓 종료
        server_socket.close()
        client_socket.close()
