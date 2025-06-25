"""서비스 레이어 테스트"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date, timedelta

from services import PenaltyService, WorkoutService, ReportService
from models import UserSettings, WeeklyProgress


class TestPenaltyService:
    """PenaltyService 테스트"""

    def test_calculate_penalty_goal_achieved(self, penalty_service):
        """목표 달성 시 벌금 계산 테스트"""
        penalty = penalty_service.calculate_penalty(5, 5)
        assert penalty == 0.0

    def test_calculate_penalty_goal_not_achieved(self, penalty_service):
        """목표 미달성 시 벌금 계산 테스트"""
        # 5회 목표에서 3회 달성 (2회 부족)
        penalty = penalty_service.calculate_penalty(5, 3)
        expected = 2 * 1440  # 2일 * 1440원
        assert penalty == expected

    def test_calculate_penalty_no_workout(self, penalty_service):
        """운동 안함 시 벌금 계산 테스트"""
        penalty = penalty_service.calculate_penalty(5, 0)
        expected = 5 * 1440  # 5일 * 1440원
        assert penalty == expected

    def test_calculate_penalty_over_goal(self, penalty_service):
        """목표 초과 달성 시 벌금 계산 테스트"""
        penalty = penalty_service.calculate_penalty(5, 7)
        assert penalty == 0.0

    def test_get_penalty_breakdown(self, penalty_service):
        """벌금 상세 정보 테스트"""
        breakdown = penalty_service.get_penalty_breakdown(5, 3)

        assert breakdown["missed_days"] == 2
        assert breakdown["achievement_rate"] == 60.0
        assert breakdown["daily_penalty"] == 1440
        assert breakdown["total_penalty"] == 2880

    def test_get_penalty_breakdown_perfect(self, penalty_service):
        """완벽한 달성 시 상세 정보 테스트"""
        breakdown = penalty_service.get_penalty_breakdown(5, 5)

        assert breakdown["missed_days"] == 0
        assert breakdown["achievement_rate"] == 100.0
        assert breakdown["daily_penalty"] == 1440
        assert breakdown["total_penalty"] == 0


class TestWorkoutService:
    """WorkoutService 테스트"""

    @pytest.mark.asyncio
    async def test_set_user_goal_valid(self, workout_service, mock_database):
        """올바른 목표 설정 테스트"""
        mock_database.set_user_goal = AsyncMock(return_value=True)

        result = await workout_service.set_user_goal(123, "테스트유저", 5)

        assert result["success"] is True
        assert "목표가 성공적으로 설정되었습니다" in result["message"]
        mock_database.set_user_goal.assert_called_once_with(123, "테스트유저", 5)

    @pytest.mark.asyncio
    async def test_set_user_goal_invalid(self, workout_service, mock_database):
        """잘못된 목표 설정 테스트"""
        result = await workout_service.set_user_goal(123, "테스트유저", 8)

        assert result["success"] is False
        assert "목표 횟수는 1회 이상 7회 이하여야 합니다" in result["message"]

    @pytest.mark.asyncio
    async def test_set_user_goal_database_error(self, workout_service, mock_database):
        """데이터베이스 오류 시 목표 설정 테스트"""
        mock_database.set_user_goal = AsyncMock(return_value=False)

        result = await workout_service.set_user_goal(123, "테스트유저", 5)

        assert result["success"] is False
        assert "목표 설정 중 오류가 발생했습니다" in result["message"]

    @pytest.mark.asyncio
    async def test_add_workout_record_success(self, workout_service, mock_database):
        """운동 기록 추가 성공 테스트"""
        # Mock 설정
        mock_database.get_user_settings = AsyncMock(
            return_value={
                "user_id": 123,
                "username": "테스트유저",
                "weekly_goal": 5,
                "total_penalty": 0.0,
            }
        )
        mock_database.add_workout_record = AsyncMock(return_value=True)
        mock_database.get_weekly_workout_count = AsyncMock(return_value=3)

        with patch("utils.get_week_start_end") as mock_get_week:
            mock_get_week.return_value = (datetime.now(), datetime.now())

            result = await workout_service.add_workout_record(123, "테스트유저")

        assert result["success"] is True
        assert result["current_count"] == 3
        assert result["weekly_goal"] == 5
        assert result["is_goal_achieved"] is False

    @pytest.mark.asyncio
    async def test_add_workout_record_no_goal(self, workout_service, mock_database):
        """목표 미설정 시 운동 기록 추가 테스트"""
        mock_database.get_user_settings = AsyncMock(return_value=None)

        result = await workout_service.add_workout_record(123, "테스트유저")

        assert result["success"] is False
        assert "먼저 주간 목표를 설정해주세요" in result["message"]

    @pytest.mark.asyncio
    async def test_add_workout_record_duplicate(self, workout_service, mock_database):
        """중복 운동 기록 추가 테스트"""
        mock_database.get_user_settings = AsyncMock(
            return_value={
                "user_id": 123,
                "username": "테스트유저",
                "weekly_goal": 5,
                "total_penalty": 0.0,
            }
        )
        mock_database.add_workout_record = AsyncMock(return_value=False)

        with patch("utils.get_week_start_end") as mock_get_week:
            mock_get_week.return_value = (datetime.now(), datetime.now())

            result = await workout_service.add_workout_record(123, "테스트유저")

        assert result["success"] is False
        assert "이미 오늘 운동을 기록했습니다" in result["message"]

    @pytest.mark.asyncio
    async def test_get_weekly_progress(self, workout_service, mock_database):
        """주간 진행 상황 조회 테스트"""
        mock_database.get_user_settings = AsyncMock(
            return_value={
                "user_id": 123,
                "username": "테스트유저",
                "weekly_goal": 5,
                "total_penalty": 1500.0,
            }
        )
        mock_database.get_weekly_workout_count = AsyncMock(return_value=3)

        with patch("utils.get_week_start_end") as mock_get_week:
            mock_get_week.return_value = (datetime.now(), datetime.now())

            progress = await workout_service.get_weekly_progress(123)

        assert progress is not None
        assert progress.user_id == 123
        assert progress.username == "테스트유저"
        assert progress.weekly_goal == 5
        assert progress.current_count == 3

    @pytest.mark.asyncio
    async def test_revoke_workout_record_success(self, workout_service, mock_database):
        """운동 기록 취소 성공 테스트"""
        mock_database.revoke_workout_record = AsyncMock(return_value=True)

        result = await workout_service.revoke_workout_record(123, datetime.now())

        assert result["success"] is True
        assert "운동 기록이 취소되었습니다" in result["message"]

    @pytest.mark.asyncio
    async def test_revoke_workout_record_not_found(
        self, workout_service, mock_database
    ):
        """취소할 운동 기록 없음 테스트"""
        mock_database.revoke_workout_record = AsyncMock(return_value=False)

        result = await workout_service.revoke_workout_record(123, datetime.now())

        assert result["success"] is False
        assert "취소할 운동 기록을 찾을 수 없습니다" in result["message"]

    @pytest.mark.asyncio
    async def test_admin_add_workout_record_success(
        self, workout_service, mock_database
    ):
        """관리자 운동 기록 추가 성공 테스트"""
        mock_database.get_user_settings = AsyncMock(
            return_value={
                "user_id": 456,
                "username": "대상유저",
                "weekly_goal": 5,
                "total_penalty": 0.0,
            }
        )
        mock_database.add_workout_record = AsyncMock(return_value=True)
        mock_database.get_weekly_workout_count = AsyncMock(
            side_effect=[2, 3]
        )  # 이전, 이후

        target_date = datetime.now() - timedelta(days=1)

        with patch("utils.get_week_start_end") as mock_get_week:
            mock_get_week.return_value = (datetime.now(), datetime.now())

            result = await workout_service.admin_add_workout_record(
                456, "대상유저", target_date
            )

        assert result["success"] is True
        assert result["previous_count"] == 2
        assert result["new_count"] == 3


class TestReportService:
    """ReportService 테스트"""

    @pytest.mark.asyncio
    async def test_get_user_weekly_summary_success(self, report_service, mock_database):
        """사용자 주간 요약 성공 테스트"""
        mock_database.get_user_settings = AsyncMock(
            return_value={
                "user_id": 123,
                "username": "테스트유저",
                "weekly_goal": 5,
                "total_penalty": 1500.0,
            }
        )
        mock_database.get_weekly_workout_count = AsyncMock(return_value=3)

        with patch("utils.get_week_start_end") as mock_get_week, patch(
            "utils.create_progress_bar"
        ) as mock_progress_bar:
            mock_get_week.return_value = (datetime.now(), datetime.now())
            mock_progress_bar.return_value = "███▒▒ 60%"

            summary = await report_service.get_user_weekly_summary(123)

        assert summary["success"] is True
        assert summary["username"] == "테스트유저"
        assert summary["current_count"] == 3
        assert summary["weekly_goal"] == 5
        assert summary["weekly_penalty"] == 2880  # (5-3) * 1440
        assert summary["total_penalty"] == 1500.0
        assert summary["achievement_rate"] == 60.0
        assert summary["is_goal_achieved"] is False

    @pytest.mark.asyncio
    async def test_get_user_weekly_summary_not_found(
        self, report_service, mock_database
    ):
        """사용자 설정 없음 테스트"""
        mock_database.get_user_settings = AsyncMock(return_value=None)

        summary = await report_service.get_user_weekly_summary(123)

        assert summary["success"] is False
        assert "사용자 설정을 찾을 수 없습니다" in summary["message"]

    @pytest.mark.asyncio
    async def test_generate_weekly_report_success(self, report_service, mock_database):
        """주간 리포트 생성 성공 테스트"""
        mock_database.get_all_users_weekly_data = AsyncMock(
            return_value=[
                {
                    "user_id": 123,
                    "username": "유저1",
                    "weekly_goal": 5,
                    "workout_count": 3,
                    "total_penalty": 1000.0,
                },
                {
                    "user_id": 456,
                    "username": "유저2",
                    "weekly_goal": 4,
                    "workout_count": 4,
                    "total_penalty": 500.0,
                },
            ]
        )

        with patch("utils.get_week_start_end") as mock_get_week, patch(
            "utils.create_progress_bar"
        ) as mock_progress_bar:
            mock_get_week.return_value = (datetime.now(), datetime.now())
            mock_progress_bar.return_value = "███▒▒ 60%"

            report = await report_service.generate_weekly_report()

        assert report["success"] is True
        assert len(report["user_reports"]) == 2
        assert report["total_weekly_penalty"] == 2880  # (5-3) * 1440
        assert report["total_accumulated_penalty"] == 4380  # 1000 + 500 + 2880

    @pytest.mark.asyncio
    async def test_save_weekly_penalties_success(self, report_service, mock_database):
        """주간 벌금 저장 성공 테스트"""
        user_reports = [
            {
                "user_id": 123,
                "username": "유저1",
                "weekly_goal": 5,
                "current_count": 3,
                "weekly_penalty": 2880,
            }
        ]

        mock_database.add_weekly_penalty_record = AsyncMock(return_value=True)
        mock_database.get_user_settings = AsyncMock(
            return_value={"total_penalty": 1000.0}
        )
        mock_database.supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            Mock()
        )

        with patch("utils.get_week_start_end") as mock_get_week:
            mock_get_week.return_value = (datetime.now(), datetime.now())

            result = await report_service.save_weekly_penalties(user_reports)

        assert result["success"] is True
        assert result["saved_count"] == 1
