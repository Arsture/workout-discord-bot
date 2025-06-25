"""
날짜 관련 유틸리티 함수
"""

from datetime import datetime, timedelta
from typing import Tuple


def get_week_start_end(date: datetime = None) -> Tuple[datetime, datetime]:
    """
    주어진 날짜가 속한 주의 시작(월요일)과 끝(일요일)을 반환

    Args:
        date: 기준 날짜 (없으면 현재 날짜)

    Returns:
        (주 시작일, 주 종료일) 튜플
    """
    if date is None:
        date = datetime.now()

    # 월요일을 0으로 하는 weekday() 사용
    days_since_monday = date.weekday()

    # 이번 주 월요일 00:00:00
    week_start = date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=days_since_monday
    )

    # 이번 주 일요일 23:59:59
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    return week_start, week_end


def get_today_date() -> datetime:
    """
    오늘 날짜를 00:00:00으로 반환
    """
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def get_korean_weekday_name(weekday: int) -> str:
    """
    요일 번호를 한국어 요일명으로 변환

    Args:
        weekday: 0(월요일) ~ 6(일요일)

    Returns:
        한국어 요일명
    """
    korean_weekdays = [
        "월요일",
        "화요일",
        "수요일",
        "목요일",
        "금요일",
        "토요일",
        "일요일",
    ]
    return korean_weekdays[weekday]


def format_date_korean(date: datetime) -> str:
    """
    날짜를 한국어 형식으로 포맷팅

    Args:
        date: 포맷팅할 날짜

    Returns:
        한국어 형식 날짜 문자열 (예: 1월 15일)
    """
    return date.strftime("%m월 %d일")
