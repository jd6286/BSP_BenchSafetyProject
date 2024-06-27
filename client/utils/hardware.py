"""
라즈베리 파이 하드웨어 제어 모듈
"""
import time
import threading

import RPi.GPIO as GPIO


class PiHardware:
    # GPIO 핀 번호
    BUZZER_PIN = 18
    def __init__(self):
        # GPIO 초기화
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUZZER_PIN, GPIO.OUT)

        self.buzzer_pwm = GPIO.PWM(self.BUZZER_PIN, 500)
        self.buzzer_state = False
        self.buzzer_thread = None

        # 초기 상태 설정
        self.buzzer_pwm.stop()
        GPIO.output(self.BUZZER_PIN, GPIO.LOW)

    def __del__(self):
        GPIO.cleanup()

    def _do_buzz(self, duration: float):
        while self.buzzer_state:
            self.buzzer_pwm.start(50)
            time.sleep(duration)

            self.buzzer_pwm.stop()
            GPIO.output(self.BUZZER_PIN, GPIO.LOW)
            time.sleep(duration)
    
    def buzzer_on(self, duration: float):
        if self.buzzer_state == False:
            self.buzzer_state = True
            self.buzzer_thread = threading.Thread(target=self._do_buzz, args=(duration,))
            self.buzzer_thread.start()
    
    def buzzer_off(self):
        self.buzzer_state = False
        self.buzzer_pwm.stop()
        GPIO.output(self.BUZZER_PIN, GPIO.LOW)   
