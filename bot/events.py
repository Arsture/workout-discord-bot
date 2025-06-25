"""
디스코드 봇 이벤트 핸들러
"""

import logging
import discord
from typing import TYPE_CHECKING
from config import WORKOUT_CHANNEL_NAME
from utils.validation import is_image_file
from utils.formatting import format_currency, create_progress_bar

if TYPE_CHECKING:
    from bot.client import WorkoutBot

logger = logging.getLogger(__name__)


class EventHandler:
    """디스코드 이벤트 처리 클래스"""

    def __init__(self, bot: "WorkoutBot"):
        self.bot = bot

    async def handle_message(self, message: discord.Message):
        """메시지 이벤트 처리"""
        # 봇 자신의 메시지는 무시
        if message.author.bot:
            return

        # 운동 채널에서의 이미지 업로드만 처리
        if message.channel.name != WORKOUT_CHANNEL_NAME:
            return

        # 첨부파일이 있는 경우만 처리
        if not message.attachments:
            return

        # 이미지 첨부파일 처리
        for attachment in message.attachments:
            if is_image_file(attachment.filename):
                await self.handle_workout_photo(message, attachment)
                break  # 첫 번째 이미지만 처리

    async def handle_workout_photo(
        self, message: discord.Message, attachment: discord.Attachment
    ):
        """운동 사진 업로드 처리"""
        try:
            user_id = message.author.id
            username = message.author.display_name

            logger.info(f"운동 사진 업로드 감지: {username} - {attachment.filename}")

            # 운동 서비스를 통해 사진 업로드 처리
            result = await self.bot.workout_service.process_photo_upload(
                user_id, username, attachment.filename
            )

            if result["success"]:
                await self._send_workout_success_message(message, result)
            else:
                await self._send_workout_error_message(message, result["message"])

        except Exception as e:
            logger.error(f"운동 사진 처리 중 오류: {e}")
            await self._send_workout_error_message(
                message,
                "운동 기록 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            )

    async def _send_workout_success_message(
        self, message: discord.Message, result: dict
    ):
        """운동 기록 성공 메시지 전송"""
        current_count = result["current_count"]
        weekly_goal = result["weekly_goal"]
        penalty_amount = result.get("penalty_amount", 0)

        # 임베드 생성
        embed = discord.Embed(
            title="🎉 운동 기록 추가 완료!",
            description=f"{message.author.mention}님의 오늘 운동이 기록되었습니다!",
            color=0x00FF00,
        )

        # 진행 상황 표시
        progress_bar = create_progress_bar(current_count, weekly_goal)
        embed.add_field(name="📈 이번 주 진행 상황", value=progress_bar, inline=False)

        # 현재 벌금 상황
        if penalty_amount > 0:
            embed.add_field(
                name="💰 현재 예상 벌금",
                value=format_currency(penalty_amount),
                inline=True,
            )

            # 남은 목표 표시
            remaining = weekly_goal - current_count
            if remaining > 0:
                embed.add_field(
                    name="🎯 남은 목표", value=f"{remaining}회", inline=True
                )
        else:
            embed.add_field(name="💰 현재 예상 벌금", value="**0원** 🎉", inline=True)

        # 목표 달성 축하 메시지
        if result.get("is_goal_achieved", False):
            embed.add_field(
                name="🏆 축하합니다!",
                value="이번 주 목표를 달성했습니다! 🎊",
                inline=False,
            )

        embed.set_footer(text="💪 꾸준한 운동으로 건강을 지켜요!")

        try:
            await message.reply(embed=embed, mention_author=False)
        except discord.Forbidden:
            # 권한이 없는 경우 일반 메시지로 전송
            await message.channel.send(
                f"🎉 {message.author.mention}님의 운동이 기록되었습니다! "
                f"({current_count}/{weekly_goal}회)"
            )

    async def _send_workout_error_message(
        self, message: discord.Message, error_message: str
    ):
        """운동 기록 오류 메시지 전송"""
        embed = discord.Embed(
            title="⚠️ 운동 기록 실패", description=error_message, color=0xFF9900
        )

        try:
            await message.reply(embed=embed, mention_author=False)
        except discord.Forbidden:
            # 권한이 없는 경우 일반 메시지로 전송
            await message.channel.send(f"⚠️ {message.author.mention} {error_message}")

    async def handle_member_join(self, member: discord.Member):
        """새 멤버 참가 시 환영 메시지"""
        try:
            # 환영 메시지용 채널 찾기
            welcome_channel = None

            # 일반 채널 또는 운동 채널에 환영 메시지 전송
            for channel in member.guild.text_channels:
                if channel.name in ["일반", "general", WORKOUT_CHANNEL_NAME]:
                    welcome_channel = channel
                    break

            if welcome_channel:
                embed = discord.Embed(
                    title="🏋️‍♀️ 운동 벌금 봇에 오신 것을 환영합니다!",
                    description=(
                        f"{member.mention}님, 안녕하세요!\n\n"
                        "**사용법:**\n"
                        "1. `/set-goals` 명령어로 주간 운동 목표를 설정하세요 (4-7회)\n"
                        f"2. #{WORKOUT_CHANNEL_NAME} 채널에 운동 사진을 올리면 자동으로 기록됩니다\n"
                        "3. `/get-info` 명령어로 현재 진행 상황을 확인할 수 있습니다\n\n"
                        "💪 함께 건강한 습관을 만들어 나가요!"
                    ),
                    color=0x4169E1,
                )

                await welcome_channel.send(embed=embed)
                logger.info(f"환영 메시지 전송: {member.display_name}")

        except Exception as e:
            logger.error(f"환영 메시지 전송 실패: {e}")

    async def handle_member_remove(self, member: discord.Member):
        """멤버 탈퇴 시 로그"""
        logger.info(f"멤버 탈퇴: {member.display_name} (ID: {member.id})")

    def register_events(self):
        """이벤트 핸들러를 봇에 등록"""

        @self.bot.event
        async def on_message(message):
            await self.handle_message(message)
            # 다른 명령어 처리를 위해 process_commands 호출
            await self.bot.process_commands(message)

        @self.bot.event
        async def on_member_join(member):
            await self.handle_member_join(member)

        @self.bot.event
        async def on_member_remove(member):
            await self.handle_member_remove(member)
