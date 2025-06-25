"""
리포트 서비스
주간 리포트 생성과 관련된 모든 비즈니스 로직을 처리합니다.
"""

import discord
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz
from database import Database
from services.penalty_service import PenaltyService
from utils.formatting import format_currency, create_progress_bar, format_date_korean
from config import REPORT_TIMEZONE


class ReportService:
    """리포트 생성 서비스"""

    def __init__(self, database: Database, penalty_service: PenaltyService):
        self.db = database
        self.penalty_service = penalty_service

    async def generate_weekly_report_data(
        self, week_start_date: datetime
    ) -> Dict[str, any]:
        """
        주간 리포트 데이터 생성

        Args:
            week_start_date: 주 시작일

        Returns:
            리포트 데이터
        """
        # 해당 주의 모든 사용자 데이터 조회
        users_data = await self.db.get_all_users_weekly_data(week_start_date)

        if not users_data:
            return {"success": False, "message": "해당 기간에 운동 데이터가 없습니다."}

        # 벌금 계산
        report_data = self.penalty_service.calculate_weekly_penalties(users_data)

        # 총합 계산
        total_weekly_penalty = sum(item["weekly_penalty"] for item in report_data)
        total_accumulated_penalty = await self.db.get_total_accumulated_penalty()

        return {
            "success": True,
            "week_start": week_start_date,
            "week_end": week_start_date + timedelta(days=6),
            "report_data": report_data,
            "total_weekly_penalty": total_weekly_penalty,
            "total_accumulated_penalty": total_accumulated_penalty,
            "participant_count": len(report_data),
        }

    def create_weekly_report_embed(self, report_data: Dict[str, any]) -> discord.Embed:
        """
        주간 리포트 Discord Embed 생성

        Args:
            report_data: 리포트 데이터

        Returns:
            Discord Embed 객체
        """
        week_start = report_data["week_start"]
        week_end = report_data["week_end"]

        week_start_str = format_date_korean(week_start)
        week_end_str = format_date_korean(week_end)

        embed = discord.Embed(
            title="📊 주간 운동 리포트",
            description=f"**{week_start_str} ~ {week_end_str}** 운동 결과",
            color=0x4169E1,
            timestamp=datetime.now(),
        )

        # 개별 사용자 결과
        user_results = []
        for user_data in report_data["report_data"]:
            username = user_data["username"]
            goal = user_data["goal"]
            actual = user_data["actual"]
            weekly_penalty = user_data["weekly_penalty"]
            total_penalty = user_data["total_penalty"]

            # 달성률 계산
            achievement_rate = (actual / goal * 100) if goal > 0 else 0

            # 상태 이모지
            if actual >= goal:
                status_emoji = "🎉"
            elif actual >= goal * 0.7:  # 70% 이상
                status_emoji = "😅"
            else:
                status_emoji = "😭"

            user_result = (
                f"{status_emoji} **{username}**\n"
                f"목표: {goal}회 → 실제: {actual}회 ({achievement_rate:.0f}%)\n"
                f"이번 주 벌금: {format_currency(weekly_penalty)}\n"
                f"누적 벌금: {format_currency(total_penalty)}"
            )
            user_results.append(user_result)

        # 사용자 결과를 필드로 추가 (최대 25개 필드 제한)
        max_users_per_field = 3
        for i in range(0, len(user_results), max_users_per_field):
            field_users = user_results[i : i + max_users_per_field]
            field_name = (
                f"👥 참가자 {i//max_users_per_field + 1}"
                if len(user_results) > max_users_per_field
                else "👥 참가자"
            )
            embed.add_field(
                name=field_name, value="\n\n".join(field_users), inline=True
            )

        # 요약 정보
        embed.add_field(
            name="📈 이번 주 요약",
            value=(
                f"총 참가자: {report_data['participant_count']}명\n"
                f"이번 주 총 벌금: **{format_currency(report_data['total_weekly_penalty'])}**\n"
                f"전체 누적 벌금: **{format_currency(report_data['total_accumulated_penalty'])}**"
            ),
            inline=False,
        )

        embed.set_footer(text="💪 꾸준한 운동으로 건강한 삶을 만들어요!")

        return embed

    async def process_weekly_penalty_records(
        self, week_start_date: datetime
    ) -> Dict[str, any]:
        """
        주간 벌금 기록 처리 (벌금 DB 저장 및 누적)

        Args:
            week_start_date: 주 시작일

        Returns:
            처리 결과
        """
        users_data = await self.db.get_all_users_weekly_data(week_start_date)

        if not users_data:
            return {"success": False, "message": "처리할 사용자 데이터가 없습니다."}

        processed_count = 0
        total_penalty_added = 0

        for user_data in users_data:
            user_id = user_data["user_id"]
            username = user_data["username"]
            weekly_goal = user_data["weekly_goal"]
            workout_count = user_data["workout_count"]

            # 벌금 계산
            weekly_penalty = self.penalty_service.calculate_penalty(
                weekly_goal, workout_count
            )

            # 벌금 기록 저장 및 누적 (원자적 처리)
            if weekly_penalty > 0:
                was_penalty_added = await self.db.add_weekly_penalty_record(
                    user_id,
                    username,
                    week_start_date,
                    weekly_goal,
                    workout_count,
                    weekly_penalty,
                )

                if was_penalty_added:
                    processed_count += 1
                    total_penalty_added += weekly_penalty

        return {
            "success": True,
            "processed_count": processed_count,
            "total_penalty_added": total_penalty_added,
        }

    async def get_user_weekly_summary(
        self, user_id: int, week_start_date: datetime = None
    ) -> Dict[str, any]:
        """
        특정 사용자의 주간 요약 정보

        Args:
            user_id: 사용자 ID
            week_start_date: 주 시작일 (None이면 이번 주)

        Returns:
            사용자 주간 요약
        """
        if week_start_date is None:
            from utils.date_utils import get_week_start_end

            week_start_date, _ = get_week_start_end()

        user_settings = await self.db.get_user_settings(user_id)
        if not user_settings:
            return {"success": False, "message": "사용자 설정을 찾을 수 없습니다."}

        current_count = await self.db.get_weekly_workout_count(user_id, week_start_date)
        weekly_goal = user_settings["weekly_goal"]
        total_penalty = user_settings["total_penalty"]

        # 벌금 계산
        weekly_penalty = self.penalty_service.calculate_penalty(
            weekly_goal, current_count
        )

        # 진행률 바 생성
        progress_bar = create_progress_bar(current_count, weekly_goal)

        return {
            "success": True,
            "username": user_settings["username"],
            "current_count": current_count,
            "weekly_goal": weekly_goal,
            "weekly_penalty": weekly_penalty,
            "total_penalty": total_penalty,
            "progress_bar": progress_bar,
            "achievement_rate": (
                (current_count / weekly_goal * 100) if weekly_goal > 0 else 0
            ),
            "is_goal_achieved": current_count >= weekly_goal,
        }

    def get_last_week_date(self) -> datetime:
        """
        지난 주 월요일 날짜 계산

        Returns:
            지난 주 월요일 datetime
        """
        now = datetime.now(pytz.timezone(REPORT_TIMEZONE))
        last_week_start = now - timedelta(days=now.weekday() + 7)  # 지난 주 월요일
        return last_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
