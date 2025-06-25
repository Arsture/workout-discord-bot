"""
운동 관련 슬래시 커맨드
"""

import logging
import discord
from typing import TYPE_CHECKING
from utils.formatting import format_currency, create_progress_bar
from config import WORKOUT_CHANNEL_NAME

if TYPE_CHECKING:
    from bot.client import WorkoutBot

logger = logging.getLogger(__name__)


def setup_workout_commands(bot: "WorkoutBot"):
    """운동 관련 슬래시 커맨드 설정"""

    @bot.tree.command(
        name="set-goals", description="주간 운동 목표를 설정합니다 (4~7회)"
    )
    async def set_goals(interaction: discord.Interaction, count: int):
        """주간 목표 설정 슬래시 커맨드"""
        try:
            result = await bot.workout_service.set_user_goal(
                interaction.user.id, interaction.user.display_name, count
            )

            if result["success"]:
                embed = discord.Embed(
                    title="🎯 목표 설정 완료",
                    description=result["message"],
                    color=0x00FF00,
                )

                # 현재 주차 진행 상황 표시
                progress = await bot.workout_service.get_weekly_progress(
                    interaction.user.id
                )
                if progress:
                    progress_bar = create_progress_bar(
                        progress.current_count, progress.weekly_goal
                    )
                    embed.add_field(
                        name="📈 이번 주 진행 상황", value=progress_bar, inline=False
                    )

                    # 현재 벌금 상황
                    penalty = bot.penalty_service.calculate_penalty(
                        progress.weekly_goal, progress.current_count
                    )
                    embed.add_field(
                        name="💰 현재 예상 벌금",
                        value=format_currency(penalty),
                        inline=True,
                    )

                embed.add_field(
                    name="📱 사용법",
                    value=f"운동 후 #{WORKOUT_CHANNEL_NAME} 채널에 사진을 업로드하세요!",
                    inline=False,
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(
                    title="❌ 목표 설정 실패",
                    description=result["message"],
                    color=0xFF0000,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            logger.info(
                f"목표 설정 시도: {interaction.user.display_name} - {count}회 "
                f"(결과: {'성공' if result['success'] else '실패'})"
            )

        except Exception as e:
            logger.error(f"목표 설정 중 오류: {e}")
            await interaction.response.send_message(
                "목표 설정 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )

    @bot.tree.command(name="revoke", description="잘못된 운동 기록을 취소합니다")
    @discord.app_commands.describe(
        member="기록을 취소할 사용자",
        date="운동한 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)",
    )
    async def revoke(
        interaction: discord.Interaction, member: discord.Member, date: str = None
    ):
        """운동 기록 취소 슬래시 커맨드"""
        # 권한 확인 (본인이거나 관리자)
        if (
            interaction.user.id != member.id
            and not interaction.user.guild_permissions.manage_messages
        ):
            await interaction.response.send_message(
                "❌ 본인의 기록이거나 관리자 권한이 있어야 기록을 취소할 수 있습니다.",
                ephemeral=True,
            )
            return

        # 날짜 검증
        target_date = None
        if date:
            target_date = bot.workout_service.validate_workout_date(date)
            if not target_date:
                await interaction.response.send_message(
                    "❌ 날짜 형식이 올바르지 않습니다. (예: 2025-01-15)", ephemeral=True
                )
                return

        try:
            result = await bot.workout_service.revoke_workout_record(
                member.id, target_date
            )

            if result["success"]:
                embed = discord.Embed(
                    title="🔄 운동 기록 취소 완료",
                    description=result["message"],
                    color=0xFF9900,
                )

                # 현재 진행 상황
                if result["weekly_goal"] > 0:
                    progress_bar = create_progress_bar(
                        result["current_count"], result["weekly_goal"]
                    )
                    embed.add_field(
                        name="📈 현재 진행 상황", value=progress_bar, inline=False
                    )

                    # 업데이트된 벌금 정보
                    penalty = bot.penalty_service.calculate_penalty(
                        result["weekly_goal"], result["current_count"]
                    )
                    embed.add_field(
                        name="💰 현재 예상 벌금",
                        value=format_currency(penalty),
                        inline=True,
                    )

                    if result["current_count"] < result["weekly_goal"]:
                        remaining = result["weekly_goal"] - result["current_count"]
                        embed.add_field(
                            name="🎯 남은 목표", value=f"{remaining}회", inline=True
                        )

                embed.add_field(
                    name="👤 취소 요청자", value=interaction.user.mention, inline=True
                )

                await interaction.response.send_message(embed=embed)

            else:
                embed = discord.Embed(
                    title="⚠️ 취소할 기록 없음",
                    description=result["message"],
                    color=0xFFFF00,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            logger.info(
                f"운동 기록 취소: {member.display_name} - {date or '오늘'} "
                f"(요청자: {interaction.user.display_name}, 결과: {'성공' if result['success'] else '실패'})"
            )

        except Exception as e:
            logger.error(f"운동 기록 취소 중 오류: {e}")
            await interaction.response.send_message(
                "운동 기록 취소 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )
