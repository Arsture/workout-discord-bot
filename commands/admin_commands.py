"""
관리자용 슬래시 커맨드
"""

import logging
import discord
from typing import TYPE_CHECKING
from utils.formatting import format_currency, create_progress_bar
from config import ADMIN_ROLE_NAME

if TYPE_CHECKING:
    from bot.client import WorkoutBot

logger = logging.getLogger(__name__)


def setup_admin_commands(bot: "WorkoutBot"):
    """관리자용 슬래시 커맨드 설정"""

    @bot.tree.command(
        name="add-workout",
        description="관리자가 특정 날짜에 운동 기록을 수동으로 추가합니다 (관리자 전용)",
    )
    @discord.app_commands.describe(
        member="운동 기록을 추가할 사용자",
        date="운동한 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)",
    )
    async def add_workout(
        interaction: discord.Interaction, member: discord.Member, date: str = None
    ):
        """관리자용 운동 기록 수동 추가 슬래시 커맨드"""
        # 관리자 권한 확인
        if not any(role.name == ADMIN_ROLE_NAME for role in interaction.user.roles):
            await interaction.response.send_message(
                f"❌ 이 명령어는 {ADMIN_ROLE_NAME} 권한이 필요합니다.",
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
            result = await bot.workout_service.add_workout_record(
                member.id, member.display_name, target_date
            )

            if result["success"]:
                embed = discord.Embed(
                    title="✅ 운동 기록 추가 완료",
                    description=result["message"],
                    color=0x00FF00,
                )

                # 진행 상황 표시
                if result.get("weekly_goal", 0) > 0:
                    progress_bar = create_progress_bar(
                        result["current_count"], result["weekly_goal"]
                    )
                    embed.add_field(
                        name="📈 현재 진행 상황", value=progress_bar, inline=False
                    )

                    # 벌금 정보
                    penalty = bot.penalty_service.calculate_penalty(
                        result["weekly_goal"], result["current_count"]
                    )
                    embed.add_field(
                        name="💰 현재 예상 벌금",
                        value=format_currency(penalty),
                        inline=True,
                    )

                    if not result.get("is_goal_achieved", False):
                        remaining = result["weekly_goal"] - result["current_count"]
                        embed.add_field(
                            name="🎯 남은 목표", value=f"{remaining}회", inline=True
                        )

                embed.add_field(
                    name="👤 추가 요청자", value=interaction.user.mention, inline=True
                )

                embed.set_footer(text="관리자 승인된 운동 기록")

                await interaction.response.send_message(embed=embed)

            else:
                embed = discord.Embed(
                    title="⚠️ 기록 추가 실패",
                    description=result["message"],
                    color=0xFFFF00,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            logger.info(
                f"운동 기록 수동 추가: {member.display_name} - {date or '오늘'} "
                f"(요청자: {interaction.user.display_name}, 결과: {'성공' if result['success'] else '실패'})"
            )

        except Exception as e:
            logger.error(f"운동 기록 수동 추가 중 오류: {e}")
            await interaction.response.send_message(
                "운동 기록 추가 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )

    @bot.tree.command(
        name="test-report", description="주간 리포트를 채널에 전송합니다 (관리자 전용)"
    )
    async def test_report(interaction: discord.Interaction):
        """테스트용 주간 리포트 전송"""
        # 관리자 권한 확인
        if not any(role.name == ADMIN_ROLE_NAME for role in interaction.user.roles):
            await interaction.response.send_message(
                f"❌ 이 명령어는 {ADMIN_ROLE_NAME} 권한이 필요합니다.",
                ephemeral=True,
            )
            return

        try:
            await interaction.response.send_message(
                "📊 주간 리포트를 생성하여 채널에 전송합니다...", ephemeral=True
            )

            # 지난 주 데이터로 리포트 생성
            last_week_date = bot.report_service.get_last_week_date()

            # 리포트 데이터 생성
            report_data = await bot.report_service.generate_weekly_report_data(
                last_week_date
            )

            if not report_data["success"]:
                await interaction.followup.send(
                    f"❌ 리포트 생성 실패: {report_data['message']}", ephemeral=True
                )
                return

            # 리포트 전송
            await bot._send_report_to_channels(report_data)

            await interaction.followup.send(
                "✅ 주간 리포트가 성공적으로 전송되었습니다!", ephemeral=True
            )

            logger.info(f"수동 주간 리포트 전송: {interaction.user.display_name}")

        except Exception as e:
            logger.error(f"수동 주간 리포트 전송 중 오류: {e}")
            await interaction.followup.send(
                "주간 리포트 전송 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )

    @bot.tree.command(
        name="reset-db", description="데이터베이스를 초기화합니다 (관리자 전용)"
    )
    @discord.app_commands.describe(
        confirmation="데이터베이스를 초기화하려면 '초기화'를 입력하세요."
    )
    async def reset_db(interaction: discord.Interaction, confirmation: str):
        """데이터베이스 초기화 (위험한 명령어)"""
        # 관리자 권한 확인
        if not any(role.name == ADMIN_ROLE_NAME for role in interaction.user.roles):
            await interaction.response.send_message(
                f"❌ 이 명령어는 {ADMIN_ROLE_NAME} 권한이 필요합니다.",
                ephemeral=True,
            )
            return

        # 확인 문구 검증
        if confirmation != "초기화":
            await interaction.response.send_message(
                "❌ 데이터베이스를 초기화하려면 정확히 '초기화'를 입력해주세요.",
                ephemeral=True,
            )
            return

        try:
            # 경고 메시지 먼저 전송
            embed = discord.Embed(
                title="⚠️ 데이터베이스 초기화 중...",
                description="**모든 데이터가 삭제됩니다!**\n잠시만 기다려주세요...",
                color=0xFF0000,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            # 데이터베이스 초기화 실행
            success = await bot.db.reset_database()

            if success:
                embed = discord.Embed(
                    title="✅ 데이터베이스 초기화 완료",
                    description=(
                        "모든 데이터가 성공적으로 삭제되었습니다.\n"
                        "사용자들은 다시 `/set-goals` 명령어로 목표를 설정해야 합니다."
                    ),
                    color=0x00FF00,
                )

                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.warning(
                    f"데이터베이스 초기화 실행: {interaction.user.display_name}"
                )
            else:
                embed = discord.Embed(
                    title="❌ 데이터베이스 초기화 실패",
                    description="초기화 중 오류가 발생했습니다. 로그를 확인해주세요.",
                    color=0xFF0000,
                )

                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"데이터베이스 초기화 중 오류: {e}")
            await interaction.followup.send(
                "데이터베이스 초기화 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )
