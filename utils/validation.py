"""
검증 관련 유틸리티 함수
"""

from datetime import datetime
from typing import Optional
from config import MIN_WEEKLY_GOAL, MAX_WEEKLY_GOAL


def validate_date_format(date_str: str) -> Optional[datetime]:
    """
    날짜 문자열 형식 검증 및 변환

    Args:
        date_str: YYYY-MM-DD 형식의 날짜 문자열

    Returns:
        변환된 datetime 객체 또는 None (실패시)
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def validate_goal_range(goal: int) -> bool:
    """
    목표 횟수가 유효한 범위인지 검증

    Args:
        goal: 주간 목표 횟수

    Returns:
        유효성 여부
    """
    return MIN_WEEKLY_GOAL <= goal <= MAX_WEEKLY_GOAL


def validate_user_id(user_id: int) -> bool:
    """
    디스코드 사용자 ID 검증

    Args:
        user_id: 디스코드 사용자 ID

    Returns:
        유효성 여부
    """
    return isinstance(user_id, int) and user_id > 0


def validate_penalty_amount(amount: float) -> bool:
    """
    벌금 금액 검증

    Args:
        amount: 벌금 금액

    Returns:
        유효성 여부
    """
    return isinstance(amount, (int, float)) and amount >= 0


def is_image_file(filename: str) -> bool:
    """
    파일이 이미지인지 확인

    Args:
        filename: 파일명

    Returns:
        이미지 파일 여부
    """
    from config import SUPPORTED_IMAGE_EXTENSIONS

    if not filename:
        return False

    # 파일 확장자 추출 및 소문자 변환
    extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
    return extension in SUPPORTED_IMAGE_EXTENSIONS


def validate_username(username: str) -> bool:
    """
    사용자명 검증

    Args:
        username: 사용자명

    Returns:
        유효성 여부
    """
    return isinstance(username, str) and len(username.strip()) > 0
