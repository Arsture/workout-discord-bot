"""통합 테스트 - 실제 외부 의존성을 사용하는 테스트"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from database import Database
from services import PenaltyService, WorkoutService, ReportService
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


@pytest.mark.integration
class TestDatabaseIntegration:
    """실제 Supabase 데이터베이스를 사용한 통합 테스트"""

    @pytest.fixture(autouse=True)
    def setup_integration_test(self):
        """통합 테스트 전후 설정"""
        # 실제 환경변수가 있는지 확인
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            pytest.skip("Supabase 환경변수가 설정되지 않았습니다")

        # 테스트용 사용자 ID (실제로는 존재하지 않을 높은 숫자)
        self.test_user_id = 999999999
        self.test_username = "통합테스트유저"

        yield

        # 테스트 후 정리 (선택사항)
        # 실제 운영 환경에서는 주의해서 사용

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """데이터베이스 연결 테스트"""
        db = Database()
        await db.init_db()
        # 연결 성공 시 예외가 발생하지 않아야 함

    @pytest.mark.asyncio
    async def test_user_goal_workflow(self):
        """사용자 목표 설정 워크플로 테스트"""
        db = Database()
        await db.init_db()

        # 1. 목표 설정
        success = await db.set_user_goal(self.test_user_id, self.test_username, 5)
        assert success is True

        # 2. 설정 조회
        user_settings = await db.get_user_settings(self.test_user_id)
        assert user_settings is not None
        assert user_settings["username"] == self.test_username
        assert user_settings["weekly_goal"] == 5
        assert user_settings["total_penalty"] == 0.0

    @pytest.mark.asyncio
    async def test_workout_record_workflow(self):
        """운동 기록 워크플로 테스트"""
        db = Database()
        await db.init_db()

        # 목표 설정
        await db.set_user_goal(self.test_user_id, self.test_username, 5)

        from utils import get_week_start_end

        week_start, _ = get_week_start_end()
        today = datetime.now()

        # 1. 운동 기록 추가
        success = await db.add_workout_record(
            self.test_user_id, self.test_username, today, week_start
        )
        assert success is True

        # 2. 중복 기록 시도 (실패해야 함)
        duplicate_success = await db.add_workout_record(
            self.test_user_id, self.test_username, today, week_start
        )
        assert duplicate_success is False

        # 3. 주간 운동 횟수 확인
        count = await db.get_weekly_workout_count(self.test_user_id, week_start)
        assert count >= 1

        # 4. 운동 기록 취소
        revoke_success = await db.revoke_workout_record(self.test_user_id, today)
        assert revoke_success is True

        # 5. 취소 후 중복 취소 시도 (실패해야 함)
        duplicate_revoke = await db.revoke_workout_record(self.test_user_id, today)
        assert duplicate_revoke is False


@pytest.mark.integration
class TestServiceIntegration:
    """서비스 레이어 통합 테스트"""

    @pytest.fixture(autouse=True)
    def setup_service_test(self):
        """서비스 테스트 설정"""
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            pytest.skip("Supabase 환경변수가 설정되지 않았습니다")

        self.test_user_id = 999999998
        self.test_username = "서비스테스트유저"

        # 실제 서비스 인스턴스 생성
        self.db = Database()
        self.penalty_service = PenaltyService()
        self.workout_service = WorkoutService(self.db, self.penalty_service)
        self.report_service = ReportService(self.db, self.penalty_service)

    @pytest.mark.asyncio
    async def test_complete_workout_cycle(self):
        """완전한 운동 사이클 테스트"""
        await self.db.init_db()

        # 1. 목표 설정
        result = await self.workout_service.set_user_goal(
            self.test_user_id, self.test_username, 5
        )
        assert result["success"] is True

        # 2. 운동 기록 추가
        result = await self.workout_service.add_workout_record(
            self.test_user_id, self.test_username
        )
        assert result["success"] is True
        assert result["current_count"] >= 1

        # 3. 주간 진행 상황 조회
        progress = await self.workout_service.get_weekly_progress(self.test_user_id)
        assert progress is not None
        assert progress.weekly_goal == 5
        assert progress.current_count >= 1

        # 4. 사용자 주간 요약 조회
        summary = await self.report_service.get_user_weekly_summary(self.test_user_id)
        assert summary["success"] is True
        assert summary["username"] == self.test_username

    @pytest.mark.asyncio
    async def test_admin_add_workout_integration(self):
        """관리자 운동 기록 추가 통합 테스트"""
        await self.db.init_db()

        # 목표 설정
        await self.workout_service.set_user_goal(
            self.test_user_id, self.test_username, 5
        )

        # 어제 날짜로 관리자 기록 추가
        yesterday = datetime.now() - timedelta(days=1)
        result = await self.workout_service.admin_add_workout_record(
            self.test_user_id, self.test_username, yesterday
        )

        assert result["success"] is True
        assert "previous_count" in result
        assert "new_count" in result
        assert result["new_count"] > result["previous_count"]


@pytest.mark.integration
class TestReportIntegration:
    """리포트 기능 통합 테스트"""

    @pytest.fixture(autouse=True)
    def setup_report_test(self):
        """리포트 테스트 설정"""
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            pytest.skip("Supabase 환경변수가 설정되지 않았습니다")

        self.db = Database()
        self.penalty_service = PenaltyService()
        self.report_service = ReportService(self.db, self.penalty_service)

    @pytest.mark.asyncio
    async def test_weekly_report_generation(self):
        """주간 리포트 생성 테스트"""
        await self.db.init_db()

        # 주간 리포트 생성
        report = await self.report_service.generate_weekly_report()

        assert report["success"] is True
        assert "user_reports" in report
        assert "total_weekly_penalty" in report
        assert "total_accumulated_penalty" in report
        assert isinstance(report["user_reports"], list)

    @pytest.mark.asyncio
    async def test_penalty_calculation_integration(self):
        """벌금 계산 통합 테스트"""
        test_cases = [
            (5, 5, 0),  # 완벽 달성
            (5, 3, 2880),  # 2회 부족
            (7, 4, 4320),  # 3회 부족
            (4, 0, 5760),  # 전혀 안함
        ]

        for goal, actual, expected_penalty in test_cases:
            penalty = self.penalty_service.calculate_penalty(goal, actual)
            assert penalty == expected_penalty

            # 상세 정보도 확인
            breakdown = self.penalty_service.get_penalty_breakdown(goal, actual)
            assert breakdown["total_penalty"] == expected_penalty


@pytest.mark.integration
class TestErrorHandling:
    """오류 처리 통합 테스트"""

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """데이터베이스 오류 처리 테스트"""
        # 잘못된 환경변수로 데이터베이스 생성
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://invalid.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "invalid_key",
            },
        ):
            with pytest.raises(Exception):
                db = Database()
                await db.init_db()

    @pytest.mark.asyncio
    async def test_service_error_propagation(self):
        """서비스 레이어 오류 전파 테스트"""
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            pytest.skip("Supabase 환경변수가 설정되지 않았습니다")

        db = Database()
        penalty_service = PenaltyService()
        workout_service = WorkoutService(db, penalty_service)

        # 존재하지 않는 사용자에 대한 운동 기록 추가 시도
        result = await workout_service.add_workout_record(999999997, "존재안함")
        assert result["success"] is False
        assert "목표를 설정해주세요" in result["message"]


@pytest.mark.integration
class TestPerformance:
    """성능 관련 통합 테스트"""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self):
        """대량 작업 성능 테스트"""
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            pytest.skip("Supabase 환경변수가 설정되지 않았습니다")

        db = Database()
        await db.init_db()

        import time

        # 여러 사용자 데이터 조회 성능 측정
        start_time = time.time()

        from utils import get_week_start_end

        week_start, _ = get_week_start_end()
        all_users_data = await db.get_all_users_weekly_data(week_start)

        end_time = time.time()
        execution_time = end_time - start_time

        # 5초 이내에 완료되어야 함 (기준은 조정 가능)
        assert execution_time < 5.0
        assert isinstance(all_users_data, list)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """동시 작업 테스트"""
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            pytest.skip("Supabase 환경변수가 설정되지 않았습니다")

        import asyncio

        db = Database()
        await db.init_db()

        # 동시에 여러 사용자 설정 조회
        user_ids = [999999991, 999999992, 999999993]

        async def get_user_setting(user_id):
            return await db.get_user_settings(user_id)

        # 동시 실행
        tasks = [get_user_setting(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 모든 작업이 완료되어야 함 (결과가 None이어도 오류가 아님)
        assert len(results) == len(user_ids)
        for result in results:
            assert not isinstance(result, Exception)
