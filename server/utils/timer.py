import datetime
import time


class Timer:
    """
    정해진 시간마다 특정 작업을 수행하는 타이머 클래스

    Args:
        timeout (int): 타임아웃 시간
    """
    def __init__(self, timeout: int = 1):
        self._is_started = False                # 타이머 시작 여부
        self._prev_time = None                  # 이전 시간
        self._count = 0                         # 타이머 카운트
        self._timeout = timeout                 # 타임아웃 시간
        self._on_timeout = self._default_callback   # 타임아웃 시 수행할 작업

    @property
    def timeout(self):
        return self._timeout
    
    @timeout.setter
    def timeout(self, timeout: int):
        self._timeout = timeout

        return None
    
    @property
    def on_timeout(self):
        # on_timeout은 get 불가
        raise AttributeError('on_timeout is not readable')
    
    @on_timeout.setter
    def on_timeout(self, callback):
        self._on_timeout = callback

        return None

    def _default_callback(self):
        """
        on_timeout 기본 동작
        """
        return None
    
    def start(self):
        """
        타이머를 시작합니다.
        """
        self._is_started = True
        self._prev_time = self._start_time

        return None

    def process(self):
        if not self._is_started:
            self.start()

        updated = False

        self._count += 1
        elapsed_time = time.time() - self._prev_time

        if elapsed_time >= self._timeout:
            updated = True
            self._on_timeout()
            self._prev_time = time.time()
            self._count = 0
        
        return updated
 
    def stop(self):
        self._is_started = False

        return None
