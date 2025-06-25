"""
정보 조회용 슬래시 커맨드
"""

import logging
import discord
from typing import TYPE_CHECKING
from datetime import datetime, timedelta
import pytz
from utils.formatting import format_currency, create_progress_bar, format_date_korean
from config import REPORT_TIMEZONE

if TYPE_CHECKING:
    from bot.client import WorkoutBot

logger = logging.getLogger(__name__)


def setup_info_commands(bot: "WorkoutBot"):
    """정보 조회용 슬래시 커맨드 설정"""

    @bot.tree.command(
        name="get-info", description="이번 주 운동 현황과 벌금을 조회합니다"
    )
    async def get_info(interaction: discord.Interaction):
        """운동 현황 조회 슬래시 커맨드"""
        try:
            # 사용자 주간 요약 정보 가져오기
            summary = await bot.report_service.get_user_weekly_summary(
                interaction.user.id
            )

            if not summary["success"]:
                embed = discord.Embed(
                    title="⚠️ 목표 설정 필요",
                    description="먼저 `/set-goals` 명령어로 주간 운동 목표를 설정해주세요!",
                    color=0xFFFF00,
                )
                embed.add_field(
                    name="📝 목표 설정 방법",
                    value="`/set-goals [횟수]` - 4~7회 사이에서 설정 가능",
                    inline=False,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # 상태에 따른 색상 및 이모지 결정
            current_count = summary["current_count"]
            weekly_goal = summary["weekly_goal"]

            if summary["is_goal_achieved"]:
                color = 0x00FF00  # 초록색 (목표 달성)
                status_emoji = "🎉"
                status_text = "목표 달성!"
            elif summary["weekly_penalty"] == 0:
                color = 0x00FF00  # 초록색
                status_emoji = "✅"
                status_text = "벌금 없음"
            elif summary["weekly_penalty"] <= 3000:
                color = 0xFFFF00  # 노란색 (약간 위험)
                status_emoji = "⚠️"
                status_text = "조금 부족해요"
            else:
                color = 0xFF0000  # 빨간색 (위험)
                status_emoji = "🚨"
                status_text = "더 노력하세요!"

            # 임베드 생성
            embed = discord.Embed(
                title=f"{status_emoji} {interaction.user.display_name}님의 운동 현황",
                description=f"**{status_text}** (주간 목표: {weekly_goal}회)",
                color=color,
            )

            # 기본 정보
            embed.add_field(
                name="🎯 이번 주 목표", value=f"{weekly_goal}회", inline=True
            )
            embed.add_field(
                name="💪 현재 운동 횟수", value=f"{current_count}회", inline=True
            )
            embed.add_field(
                name="📊 달성률",
                value=f"{summary['achievement_rate']:.1f}%",
                inline=True,
            )

            # 진행률 바
            embed.add_field(
                name="📈 진행 상황", value=summary["progress_bar"], inline=False
            )

            # 벌금 정보
            if summary["weekly_penalty"] > 0:
                embed.add_field(
                    name="💸 이번 주 예상 벌금",
                    value=f"**{format_currency(summary['weekly_penalty'])}**",
                    inline=True,
                )

                # 남은 기회 계산
                remaining_days = 7 - (datetime.now().weekday() + 1)
                if remaining_days > 0:
                    remaining_workouts = weekly_goal - current_count
                    embed.add_field(
                        name="⏰ 남은 기회",
                        value=f"{remaining_workouts}회 ({remaining_days}일 남음)",
                        inline=True,
                    )
            else:
                embed.add_field(
                    name="💸 이번 주 예상 벌금", value="**0원** 🎉", inline=True
                )

            embed.add_field(
                name="💰 누적 벌금",
                value=format_currency(summary["total_penalty"]),
                inline=True,
            )

            # 주차 정보
            from utils.date_utils import get_week_start_end

            week_start, week_end = get_week_start_end()
            week_start_str = format_date_korean(week_start)
            week_end_str = format_date_korean(week_end)
            embed.set_footer(
                text=f"기간: {week_start_str} ~ {week_end_str} | 💪 화이팅!"
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            logger.info(
                f"현황 조회: {interaction.user.display_name} - {current_count}/{weekly_goal}회"
            )

        except Exception as e:
            logger.error(f"현황 조회 중 오류: {e}")
            await interaction.response.send_message(
                "현황 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )

    @bot.tree.command(name="weekly-report", description="주간 운동 리포트를 조회합니다")
    @discord.app_commands.describe(
        week_offset="몇 주 전 리포트를 볼지 설정 (0=지난주, 1=지지난주, ...)"
    )
    async def weekly_report(interaction: discord.Interaction, week_offset: int = 0):
        """주간 리포트 슬래시 커맨드"""
        try:
            await interaction.response.send_message(
                "📊 주간 리포트를 생성 중입니다...", ephemeral=True
            )

            # 지정된 주차 데이터 계산
            now = datetime.now(pytz.timezone(REPORT_TIMEZONE))
            target_week_start = now - timedelta(
                days=now.weekday() + (7 * (week_offset + 1))
            )  # week_offset=0이면 지난주
            target_week_start = target_week_start.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # 리포트 데이터 생성
            report_data = await bot.report_service.generate_weekly_report_data(
                target_week_start
            )

            if not report_data["success"]:
                embed = discord.Embed(
                    title="📊 주간 리포트",
                    description=report_data["message"],
                    color=0xFFFF00,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # 리포트 임베드 생성
            embed = bot.report_service.create_weekly_report_embed(report_data)

            # 제목 수정 (몇 주 전인지 표시)
            if week_offset == 0:
                title_prefix = "📊 지난주 운동 리포트"
            else:
                title_prefix = f"📊 {week_offset + 1}주 전 운동 리포트"

            embed.title = title_prefix

            await interaction.followup.send(embed=embed, ephemeral=True)

            logger.info(
                f"주간 리포트 조회: {interaction.user.display_name} - {week_offset}주 전"
            )

        except Exception as e:
            logger.error(f"주간 리포트 조회 중 오류: {e}")
            await interaction.followup.send(
                "주간 리포트 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )
