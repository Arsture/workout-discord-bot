"""
운동 서비스
운동 기록과 관련된 모든 비즈니스 로직을 처리합니다.
"""

from typing import Optional, Dict, List
from datetime import datetime, date
from database import Database
from models.user import UserSettings
from models.workout import WorkoutRecord, WeeklyProgress
from utils.date_utils import get_week_start_end, get_today_date
from utils.validation import validate_goal_range, validate_date_format, is_image_file
from services.penalty_service import PenaltyService


class WorkoutService:
    """운동 관련 비즈니스 로직 서비스"""

    def __init__(self, database: Database, penalty_service: PenaltyService):
        self.db = database
        self.penalty_service = penalty_service

    async def set_user_goal(
        self, user_id: int, username: str, weekly_goal: int
    ) -> Dict[str, any]:
        """
        사용자 목표 설정

        Args:
            user_id: 사용자 ID
            username: 사용자명
            weekly_goal: 주간 목표

        Returns:
            설정 결과
        """
        if not validate_goal_range(weekly_goal):
            return {
                "success": False,
                "message": f"목표는 4-7회 사이여야 합니다. (입력값: {weekly_goal})",
            }

        success = await self.db.set_user_goal(user_id, username, weekly_goal)

        if success:
            return {
                "success": True,
                "message": f"주간 목표가 {weekly_goal}회로 설정되었습니다.",
                "goal": weekly_goal,
            }
        else:
            return {
                "success": False,
                "message": "목표 설정에 실패했습니다. 다시 시도해주세요.",
            }

    async def add_workout_record(
        self, user_id: int, username: str, workout_date: datetime = None
    ) -> Dict[str, any]:
        """
        운동 기록 추가

        Args:
            user_id: 사용자 ID
            username: 사용자명
            workout_date: 운동 날짜 (None이면 오늘)

        Returns:
            추가 결과
        """
        if workout_date is None:
            workout_date = get_today_date()

        # 사용자 설정 확인
        user_settings = await self.db.get_user_settings(user_id)
        if not user_settings:
            return {
                "success": False,
                "message": "먼저 `/set-goals` 명령어로 목표를 설정해주세요.",
            }

        # 주차 정보 계산
        week_start, _ = get_week_start_end(workout_date)

        # 기록 추가 시도
        success = await self.db.add_workout_record(
            user_id, username, workout_date, week_start
        )

        if success:
            # 현재 진행 상황 조회
            current_count = await self.db.get_weekly_workout_count(user_id, week_start)
            weekly_goal = user_settings["weekly_goal"]

            return {
                "success": True,
                "message": f"{workout_date.strftime('%m월 %d일')} 운동 기록이 추가되었습니다!",
                "current_count": current_count,
                "weekly_goal": weekly_goal,
                "is_goal_achieved": current_count >= weekly_goal,
            }
        else:
            return {
                "success": False,
                "message": f"{workout_date.strftime('%m월 %d일')}에 이미 운동 기록이 있습니다.",
            }

    async def revoke_workout_record(
        self, user_id: int, workout_date: datetime = None
    ) -> Dict[str, any]:
        """
        운동 기록 취소

        Args:
            user_id: 사용자 ID
            workout_date: 운동 날짜 (None이면 오늘)

        Returns:
            취소 결과
        """
        if workout_date is None:
            workout_date = get_today_date()

        success = await self.db.revoke_workout_record(user_id, workout_date)

        if success:
            # 사용자 설정 및 현재 진행 상황 조회
            user_settings = await self.db.get_user_settings(user_id)
            week_start, _ = get_week_start_end(workout_date)
            current_count = await self.db.get_weekly_workout_count(user_id, week_start)

            return {
                "success": True,
                "message": f"{workout_date.strftime('%m월 %d일')} 운동 기록이 취소되었습니다.",
                "current_count": current_count,
                "weekly_goal": user_settings["weekly_goal"] if user_settings else 0,
            }
        else:
            return {
                "success": False,
                "message": f"{workout_date.strftime('%m월 %d일')}에 취소할 운동 기록이 없습니다.",
            }

    async def get_weekly_progress(
        self, user_id: int, week_start_date: datetime = None
    ) -> Optional[WeeklyProgress]:
        """
        주간 진행 상황 조회

        Args:
            user_id: 사용자 ID
            week_start_date: 주 시작일 (None이면 이번 주)

        Returns:
            주간 진행 상황 또는 None
        """
        if week_start_date is None:
            week_start_date, _ = get_week_start_end()

        user_settings = await self.db.get_user_settings(user_id)
        if not user_settings:
            return None

        current_count = await self.db.get_weekly_workout_count(user_id, week_start_date)

        return WeeklyProgress(
            user_id=user_id,
            username=user_settings["username"],
            weekly_goal=user_settings["weekly_goal"],
            current_count=current_count,
            week_start_date=week_start_date.date(),
        )

    async def process_photo_upload(
        self, user_id: int, username: str, filename: str
    ) -> Dict[str, any]:
        """
        사진 업로드 처리

        Args:
            user_id: 사용자 ID
            username: 사용자명
            filename: 파일명

        Returns:
            처리 결과
        """
        # 이미지 파일 검증
        if not is_image_file(filename):
            return {"success": False, "message": "지원되지 않는 파일 형식입니다."}

        # 운동 기록 추가 시도
        result = await self.add_workout_record(user_id, username)

        if result["success"]:
            # 진행 상황 정보 추가
            penalty_amount = self.penalty_service.calculate_penalty(
                result["weekly_goal"], result["current_count"]
            )
            result["penalty_amount"] = penalty_amount

        return result

    def validate_workout_date(self, date_str: str) -> Optional[datetime]:
        """
        운동 날짜 문자열 검증

        Args:
            date_str: 날짜 문자열 (YYYY-MM-DD)

        Returns:
            검증된 datetime 객체 또는 None
        """
        return validate_date_format(date_str)
