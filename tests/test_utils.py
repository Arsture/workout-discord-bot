"""유틸리티 함수 테스트"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch

from utils import (
    get_week_start_end,
    format_currency,
    create_progress_bar,
    validate_goal_range,
    validate_date_format,
    format_date_korean,
    validate_user_id,
)


class TestDateUtils:
    """날짜 관련 유틸리티 테스트"""

    def test_get_week_start_end_monday(self):
        """월요일 기준 주 시작/끝 계산 테스트"""
        # 2024년 1월 17일 (수요일)을 기준으로 테스트
        test_date = datetime(2024, 1, 17, 15, 30, 0)

        week_start, week_end = get_week_start_end(test_date)

        # 주 시작은 2024년 1월 15일 (월요일) 00:00:00
        expected_start = datetime(2024, 1, 15, 0, 0, 0)

        assert week_start == expected_start
        assert week_end.date() > week_start.date()

    def test_format_date_korean(self):
        """한국어 날짜 포맷 테스트"""
        test_date = datetime(2024, 1, 17)
        formatted = format_date_korean(test_date)
        assert formatted == "01월 17일"


class TestFormatting:
    """포맷팅 관련 유틸리티 테스트"""

    def test_format_currency_zero(self):
        """0원 포맷팅 테스트"""
        result = format_currency(0)
        assert result == "0원"

    def test_format_currency_positive(self):
        """양수 포맷팅 테스트"""
        result = format_currency(1440)
        assert result == "1,440원"

    def test_create_progress_bar_basic(self):
        """진행률 바 기본 테스트"""
        result = create_progress_bar(3, 5)
        assert "3" in result
        assert "5" in result


class TestValidation:
    """유효성 검증 관련 유틸리티 테스트"""

    def test_validate_goal_range_valid(self):
        """올바른 목표 검증 테스트"""
        assert validate_goal_range(5) is True
        assert validate_goal_range(1) is True
        assert validate_goal_range(7) is True

    def test_validate_goal_range_invalid(self):
        """잘못된 목표 검증 테스트"""
        assert validate_goal_range(0) is False
        assert validate_goal_range(8) is False

    def test_validate_user_id_valid(self):
        """올바른 사용자 ID 검증 테스트"""
        assert validate_user_id(123456789) is True

    def test_validate_user_id_invalid(self):
        """잘못된 사용자 ID 검증 테스트"""
        assert validate_user_id(0) is False
        assert validate_user_id(-123) is False

    def test_validate_date_format_valid(self):
        """올바른 날짜 형식 검증 테스트"""
        result = validate_date_format("2024-01-17")
        assert result is not None
        assert isinstance(result, datetime)

    def test_validate_date_format_invalid(self):
        """잘못된 날짜 형식 검증 테스트"""
        result = validate_date_format("invalid-date")
        assert result is None
