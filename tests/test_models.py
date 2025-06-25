"""도메인 모델 테스트"""

import pytest
from datetime import datetime, date
from models import UserSettings, WorkoutRecord, WeeklyProgress


class TestUserSettings:
    """UserSettings 모델 테스트"""

    def test_user_settings_creation(self):
        """UserSettings 객체 생성 테스트"""
        user_settings = UserSettings(
            user_id=123456789,
            username="테스트유저",
            weekly_goal=5,
            total_penalty=1500.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert user_settings.user_id == 123456789
        assert user_settings.username == "테스트유저"
        assert user_settings.weekly_goal == 5
        assert user_settings.total_penalty == 1500.0

    def test_is_goal_valid(self):
        """목표 유효성 검증 테스트"""
        valid_user = UserSettings(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            total_penalty=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        invalid_user_low = UserSettings(
            user_id=123,
            username="테스트",
            weekly_goal=0,
            total_penalty=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        invalid_user_high = UserSettings(
            user_id=123,
            username="테스트",
            weekly_goal=8,
            total_penalty=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert valid_user.is_goal_valid is True
        assert invalid_user_low.is_goal_valid is False
        assert invalid_user_high.is_goal_valid is False

    def test_update_goal_valid(self):
        """올바른 목표 업데이트 테스트"""
        user_settings = UserSettings(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            total_penalty=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        user_settings.update_goal(6)
        assert user_settings.weekly_goal == 6

    def test_update_goal_invalid(self):
        """잘못된 목표 업데이트 테스트"""
        user_settings = UserSettings(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            total_penalty=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(
            ValueError, match="목표 횟수는 1회 이상 7회 이하여야 합니다"
        ):
            user_settings.update_goal(8)

        with pytest.raises(
            ValueError, match="목표 횟수는 1회 이상 7회 이하여야 합니다"
        ):
            user_settings.update_goal(0)

    def test_add_penalty(self):
        """벌금 추가 테스트"""
        user_settings = UserSettings(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            total_penalty=1000.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        user_settings.add_penalty(500.0)
        assert user_settings.total_penalty == 1500.0

    def test_add_negative_penalty(self):
        """음수 벌금 추가 테스트"""
        user_settings = UserSettings(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            total_penalty=1000.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="벌금은 0 이상이어야 합니다"):
            user_settings.add_penalty(-100.0)


class TestWorkoutRecord:
    """WorkoutRecord 모델 테스트"""

    def test_workout_record_creation(self):
        """WorkoutRecord 객체 생성 테스트"""
        record = WorkoutRecord(
            record_id=1,
            user_id=123456789,
            username="테스트유저",
            workout_date=date(2024, 1, 15),
            week_start_date=date(2024, 1, 15),
            created_at=datetime.now(),
            is_revoked=False,
        )

        assert record.record_id == 1
        assert record.user_id == 123456789
        assert record.username == "테스트유저"
        assert record.workout_date == date(2024, 1, 15)
        assert record.is_revoked is False

    def test_is_current_week(self):
        """현재 주 기록인지 확인 테스트"""
        today = date.today()
        record = WorkoutRecord(
            record_id=1,
            user_id=123,
            username="테스트",
            workout_date=today,
            week_start_date=today,
            created_at=datetime.now(),
            is_revoked=False,
        )

        assert record.is_current_week(today) is True

    def test_is_active(self):
        """활성 기록인지 확인 테스트"""
        record_active = WorkoutRecord(
            record_id=1,
            user_id=123,
            username="테스트",
            workout_date=date.today(),
            week_start_date=date.today(),
            created_at=datetime.now(),
            is_revoked=False,
        )

        record_revoked = WorkoutRecord(
            record_id=2,
            user_id=123,
            username="테스트",
            workout_date=date.today(),
            week_start_date=date.today(),
            created_at=datetime.now(),
            is_revoked=True,
        )

        assert record_active.is_active is True
        assert record_revoked.is_active is False


class TestWeeklyProgress:
    """WeeklyProgress 모델 테스트"""

    def test_weekly_progress_creation(self):
        """WeeklyProgress 객체 생성 테스트"""
        progress = WeeklyProgress(
            user_id=123456789,
            username="테스트유저",
            weekly_goal=5,
            current_count=3,
            week_start_date=date.today(),
        )

        assert progress.user_id == 123456789
        assert progress.username == "테스트유저"
        assert progress.weekly_goal == 5
        assert progress.current_count == 3

    def test_remaining_count(self):
        """남은 횟수 계산 테스트"""
        progress = WeeklyProgress(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            current_count=3,
            week_start_date=date.today(),
        )

        assert progress.remaining_count == 2

    def test_remaining_count_goal_achieved(self):
        """목표 달성 시 남은 횟수 테스트"""
        progress = WeeklyProgress(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            current_count=6,
            week_start_date=date.today(),
        )

        assert progress.remaining_count == 0

    def test_achievement_rate(self):
        """달성률 계산 테스트"""
        progress = WeeklyProgress(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            current_count=3,
            week_start_date=date.today(),
        )

        assert progress.achievement_rate == 60.0

    def test_achievement_rate_over_goal(self):
        """목표 초과 달성 시 달성률 테스트"""
        progress = WeeklyProgress(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            current_count=7,
            week_start_date=date.today(),
        )

        assert progress.achievement_rate == 140.0

    def test_is_completed(self):
        """목표 완료 여부 테스트"""
        progress_incomplete = WeeklyProgress(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            current_count=3,
            week_start_date=date.today(),
        )

        progress_complete = WeeklyProgress(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            current_count=5,
            week_start_date=date.today(),
        )

        progress_over_complete = WeeklyProgress(
            user_id=123,
            username="테스트",
            weekly_goal=5,
            current_count=7,
            week_start_date=date.today(),
        )

        assert progress_incomplete.is_completed is False
        assert progress_complete.is_completed is True
        assert progress_over_complete.is_completed is True
