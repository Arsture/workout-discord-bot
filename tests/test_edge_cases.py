"""
엣지케이스 테스트
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from services.workout_service import WorkoutService
from services.penalty_service import PenaltyService


@pytest.mark.unit
class TestWorkoutEdgeCases:
    """운동 관련 엣지케이스 테스트"""

    async def test_add_revoke_add_same_day_workflow(self, mock_database):
        """동일한 날짜에 add -> revoke -> add 워크플로우 테스트"""
        # Mock 설정
        penalty_service = PenaltyService()
        workout_service = WorkoutService(mock_database, penalty_service)

        user_id = 123
        username = "테스트유저"
        today = datetime.now()

        # 1. 사용자 설정이 있다고 가정
        mock_database.get_user_settings = AsyncMock(
            return_value={"user_id": user_id, "username": username, "weekly_goal": 5}
        )

        # 2. 첫 번째 운동 기록 추가 성공
        mock_database.add_workout_record = AsyncMock(return_value=True)
        mock_database.get_weekly_workout_count = AsyncMock(return_value=1)

        result1 = await workout_service.add_workout_record(user_id, username, today)

        assert result1["success"] is True
        assert "운동 기록이 추가되었습니다" in result1["message"]
        assert result1["current_count"] == 1

        # 3. 운동 기록 취소 성공
        mock_database.revoke_workout_record = AsyncMock(return_value=True)
        mock_database.get_weekly_workout_count = AsyncMock(
            return_value=0
        )  # 취소 후 0개

        result2 = await workout_service.revoke_workout_record(user_id, today)

        assert result2["success"] is True
        assert "운동 기록이 취소되었습니다" in result2["message"]
        assert result2["current_count"] == 0

        # 4. 다시 같은 날짜에 운동 기록 추가 시도 (성공해야 함)
        mock_database.add_workout_record = AsyncMock(
            return_value=True
        )  # 이번에는 성공해야 함
        mock_database.get_weekly_workout_count = AsyncMock(return_value=1)

        result3 = await workout_service.add_workout_record(user_id, username, today)

        assert result3["success"] is True
        assert "운동 기록이 추가되었습니다" in result3["message"]
        assert result3["current_count"] == 1

        # 호출 검증
        assert mock_database.add_workout_record.call_count == 2
        assert mock_database.revoke_workout_record.call_count == 1

    async def test_add_revoke_add_database_level_detailed(self, mock_database):
        """데이터베이스 레벨에서 더 정교한 add -> revoke -> add 테스트"""
        user_id = 123
        username = "테스트유저"
        today = datetime.now()
        week_start = today

        # Supabase 응답 객체를 모킹
        mock_response_with_data = MagicMock()
        mock_response_with_data.data = [{"id": 1, "is_revoked": False}]

        mock_response_no_data = MagicMock()
        mock_response_no_data.data = []

        mock_response_insert = MagicMock()
        mock_response_insert.data = [{"id": 1}]

        mock_response_update = MagicMock()
        mock_response_update.data = [{"id": 1, "is_revoked": True}]

        # Supabase 테이블 객체 모킹
        mock_table = MagicMock()
        mock_database.supabase.table.return_value = mock_table

        # 첫 번째 add: 중복 검사 -> 없음, 삽입 -> 성공
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            mock_response_no_data,  # 중복 검사: 기존 기록 없음
        ]
        mock_table.insert.return_value.execute.return_value = mock_response_insert

        result1 = await mock_database.add_workout_record(
            user_id, username, today, week_start
        )
        assert result1 is True

        # revoke: 기록 존재 -> 업데이트 성공
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            mock_response_with_data,  # 취소할 기록 존재
        ]
        mock_table.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response_update
        )

        result2 = await mock_database.revoke_workout_record(user_id, today)
        assert result2 is True

        # 두 번째 add: 중복 검사 -> 없음 (revoke된 기록은 제외), 삽입 -> 성공
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            mock_response_no_data,  # 중복 검사: is_revoked=False인 기록 없음
        ]
        mock_table.insert.return_value.execute.return_value = mock_response_insert

        result3 = await mock_database.add_workout_record(
            user_id, username, today, week_start
        )
        assert result3 is True

    async def test_revoke_already_revoked_record(self, mock_database):
        """이미 취소된 기록을 다시 취소하려고 할 때의 테스트"""
        user_id = 123
        today = datetime.now()

        # 취소할 기록이 없음 (이미 취소되었거나 존재하지 않음)
        mock_response_no_data = MagicMock()
        mock_response_no_data.data = []

        mock_response_revoked_data = MagicMock()
        mock_response_revoked_data.data = [{"id": 1, "is_revoked": True}]

        mock_table = MagicMock()
        mock_database.supabase.table.return_value = mock_table

        # 첫 번째 쿼리: is_revoked=False인 기록 없음
        # 두 번째 쿼리: 모든 기록 조회 (이미 취소된 기록 존재)
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            mock_response_no_data,  # is_revoked=False인 기록 없음
            mock_response_revoked_data,  # 이미 취소된 기록 존재
        ]

        result = await mock_database.revoke_workout_record(user_id, today)
        assert result is False

    async def test_multiple_revoke_same_record(self, mock_database):
        """같은 기록을 여러 번 revoke 시도하는 테스트"""
        penalty_service = PenaltyService()
        workout_service = WorkoutService(mock_database, penalty_service)

        user_id = 123
        today = datetime.now()

        # 사용자 설정
        mock_database.get_user_settings = AsyncMock(
            return_value={
                "user_id": user_id,
                "username": "테스트유저",
                "weekly_goal": 5,
            }
        )

        # 첫 번째 revoke: 성공
        mock_database.revoke_workout_record = AsyncMock(return_value=True)
        mock_database.get_weekly_workout_count = AsyncMock(return_value=0)

        result1 = await workout_service.revoke_workout_record(user_id, today)
        assert result1["success"] is True

        # 두 번째 revoke: 실패 (이미 revoke된 기록이므로)
        mock_database.revoke_workout_record = AsyncMock(return_value=False)

        result2 = await workout_service.revoke_workout_record(user_id, today)
        assert result2["success"] is False
        assert "취소할 운동 기록이 없습니다" in result2["message"]

    async def test_edge_case_same_day_multiple_operations(self, mock_database):
        """같은 날 여러 번의 add/revoke 작업 테스트"""
        penalty_service = PenaltyService()
        workout_service = WorkoutService(mock_database, penalty_service)

        user_id = 123
        username = "테스트유저"
        today = datetime.now()

        # 사용자 설정
        mock_database.get_user_settings = AsyncMock(
            return_value={"user_id": user_id, "username": username, "weekly_goal": 5}
        )

        # 시나리오: add -> revoke -> add -> revoke -> add
        operations = [
            ("add", True, 1),  # 첫 번째 추가 성공
            ("revoke", True, 0),  # 취소 성공
            ("add", True, 1),  # 두 번째 추가 성공
            ("revoke", True, 0),  # 두 번째 취소 성공
            ("add", True, 1),  # 세 번째 추가 성공
        ]

        for i, (operation, expected_success, expected_count) in enumerate(operations):
            if operation == "add":
                mock_database.add_workout_record = AsyncMock(
                    return_value=expected_success
                )
                mock_database.get_weekly_workout_count = AsyncMock(
                    return_value=expected_count
                )

                result = await workout_service.add_workout_record(
                    user_id, username, today
                )
                assert (
                    result["success"] == expected_success
                ), f"작업 {i+1} 실패: {operation}"
                if expected_success:
                    assert result["current_count"] == expected_count

            elif operation == "revoke":
                mock_database.revoke_workout_record = AsyncMock(
                    return_value=expected_success
                )
                mock_database.get_weekly_workout_count = AsyncMock(
                    return_value=expected_count
                )

                result = await workout_service.revoke_workout_record(user_id, today)
                assert (
                    result["success"] == expected_success
                ), f"작업 {i+1} 실패: {operation}"
                if expected_success:
                    assert result["current_count"] == expected_count
