"""
디버깅을 위한 모듈
"""
import datetime


def current_time():
    """
    현재 시간을 문자열로 반환합니다.

    Returns:
        str: 현재 시간 문자열
    """
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
