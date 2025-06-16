from datetime import datetime, timedelta
from typing import Tuple


def calculate_penalty(
    goal_count: int, actual_count: int, base_penalty: float = 10800.0
) -> float:
    """
    벌금 계산 함수

    Args:
        goal_count: 목표 운동 횟수
        actual_count: 실제 운동 횟수
        base_penalty: 기본 벌금 (기본값: 10,800원)

    Returns:
        계산된 벌금
    """
    if actual_count >= goal_count:
        return 0.0

    missed_count = goal_count - actual_count
    daily_penalty = base_penalty / goal_count
    total_penalty = daily_penalty * missed_count

    return total_penalty


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


def format_currency(amount: float) -> str:
    """
    금액을 한국 원화 형식으로 포맷팅

    Args:
        amount: 금액

    Returns:
        포맷팅된 금액 문자열
    """
    return f"{amount:,.0f}원"


def get_today_date() -> datetime:
    """
    오늘 날짜를 00:00:00으로 반환
    """
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
