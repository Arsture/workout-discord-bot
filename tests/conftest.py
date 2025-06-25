"""pytest 설정 및 공통 fixture"""

import os
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, date, timedelta
from typing import Dict, Any

# 테스트용 환경변수 설정
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_key"
os.environ["DISCORD_TOKEN"] = "test_token"
os.environ["WORKOUT_CHANNEL_NAME"] = "test-workout"
os.environ["REPORT_CHANNEL_NAME"] = "test-report"
os.environ["ADMIN_ROLE_NAME"] = "TestAdmin"

from database import Database
from services import PenaltyService, WorkoutService, ReportService
from models import UserSettings, WorkoutRecord, WeeklyProgress


@pytest.fixture(scope="session")
def event_loop():
    """세션 범위의 이벤트 루프 생성"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase 클라이언트"""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table

    # 기본 응답 설정
    mock_response = Mock()
    mock_response.data = []

    # 체이닝 메서드들 설정
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_database(mock_supabase_client):
    """Mock 데이터베이스 인스턴스"""
    db = Database()
    db.supabase = mock_supabase_client
    return db


@pytest.fixture
def penalty_service():
    """PenaltyService 인스턴스"""
    return PenaltyService()


@pytest.fixture
def workout_service(mock_database, penalty_service):
    """WorkoutService 인스턴스"""
    return WorkoutService(mock_database, penalty_service)


@pytest.fixture
def report_service(mock_database, penalty_service):
    """ReportService 인스턴스"""
    return ReportService(mock_database, penalty_service)


@pytest.fixture
def sample_user_settings():
    """테스트용 사용자 설정 데이터"""
    return UserSettings(
        user_id=123456789,
        username="테스트유저",
        weekly_goal=5,
        total_penalty=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_workout_record():
    """테스트용 운동 기록 데이터"""
    return WorkoutRecord(
        record_id=1,
        user_id=123456789,
        username="테스트유저",
        workout_date=date.today(),
        week_start_date=date.today(),
        created_at=datetime.now(),
        is_revoked=False,
    )


@pytest.fixture
def sample_weekly_progress():
    """테스트용 주간 진행 상황 데이터"""
    return WeeklyProgress(
        user_id=123456789,
        username="테스트유저",
        weekly_goal=5,
        current_count=3,
        week_start_date=date.today(),
    )


@pytest.fixture
def mock_supabase_response():
    """Mock Supabase 응답 생성 헬퍼"""

    def _create_response(data=None, count=None, error=None):
        response = Mock()
        response.data = data or []
        response.count = count
        response.error = error
        return response

    return _create_response


@pytest.fixture
def current_week_dates():
    """현재 주의 시작/끝 날짜"""
    from utils import get_week_start_end

    return get_week_start_end()


# 테스트 설정
pytest_plugins = []


def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "integration: Integration tests that require external dependencies"
    )
    config.addinivalue_line("markers", "unit: Unit tests that use mocks")
    config.addinivalue_line("markers", "asyncio: Async tests")
