"""
포맷팅 관련 유틸리티 함수
"""


def format_currency(amount: float) -> str:
    """
    금액을 한국 원화 형식으로 포맷팅

    Args:
        amount: 금액

    Returns:
        포맷팅된 금액 문자열
    """
    return f"{amount:,.0f}원"


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    진행률 바 생성

    Args:
        current: 현재 진행률
        total: 전체 목표
        length: 바의 길이

    Returns:
        진행률 바 문자열
    """
    if total == 0:
        return "📊 " + "⬜︎" * length

    filled = min(int((current / total) * length), length)
    empty = length - filled

    progress = "📊 " + "⬛︎" * filled + "⬜︎" * empty
    progress += f" {current}/{total}"

    return progress


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    백분율 포맷팅

    Args:
        value: 백분율 값 (0-100)
        decimal_places: 소수점 자릿수

    Returns:
        포맷팅된 백분율 문자열
    """
    return f"{value:.{decimal_places}f}%"


def format_user_mention(user_id: int) -> str:
    """
    사용자 멘션 포맷팅

    Args:
        user_id: 디스코드 사용자 ID

    Returns:
        멘션 문자열
    """
    return f"<@{user_id}>"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    텍스트 길이 제한

    Args:
        text: 원본 텍스트
        max_length: 최대 길이
        suffix: 생략 표시 문자

    Returns:
        길이가 제한된 텍스트
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_date_korean(date) -> str:
    """
    날짜를 한국어 형식으로 포맷팅

    Args:
        date: 포맷팅할 날짜

    Returns:
        한국어 형식 날짜 문자열 (예: 1월 15일)
    """
    return date.strftime("%m월 %d일")
