import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import Database
from utils import calculate_penalty, get_week_start_end, format_currency, get_today_date
from config import (
    MIN_WEEKLY_GOAL,
    MAX_WEEKLY_GOAL,
    WORKOUT_CHANNEL_NAME,
    SUPPORTED_IMAGE_EXTENSIONS,
)

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True


class WorkoutBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db = Database()
        self.scheduler = AsyncIOScheduler()

    async def setup_hook(self):
        """봇 시작 시 실행되는 설정"""
        await self.db.init_db()
        logger.info("데이터베이스 초기화 완료")

        # 스케줄러 시작
        self.scheduler.start()
        logger.info("스케줄러 시작")

        # 매주 월요일 00:00에 주간 리포트 전송
        self.scheduler.add_job(
            self.send_weekly_report,
            CronTrigger(day_of_week=0, hour=0, minute=0),  # 월요일 00:00
            id="weekly_report",
        )

        # 슬래시 커맨드 동기화
        try:
            synced = await self.tree.sync()
            logger.info(f"{len(synced)}개의 슬래시 커맨드 동기화 완료")
        except Exception as e:
            logger.error(f"슬래시 커맨드 동기화 실패: {e}")

    async def on_ready(self):
        """봇이 준비되었을 때"""
        logger.info(f"{self.user}(ID: {self.user.id})로 로그인 완료!")
        logger.info(f"서버 수: {len(self.guilds)}")

    async def send_weekly_report(self):
        """주간 벌금 리포트 전송"""
        # TODO: 구현 예정
        logger.info("주간 리포트 전송 (구현 예정)")


# 봇 인스턴스 생성
bot = WorkoutBot()


# 슬래시 커맨드 정의
@bot.tree.command(name="set-goals", description="주간 운동 목표를 설정합니다 (4~7회)")
async def set_goals(interaction: discord.Interaction, count: int):
    """운동 목표 설정 슬래시 커맨드"""
    # 입력값 검증
    if count < MIN_WEEKLY_GOAL or count > MAX_WEEKLY_GOAL:
        await interaction.response.send_message(
            f"⚠️ 운동 목표는 {MIN_WEEKLY_GOAL}회부터 {MAX_WEEKLY_GOAL}회까지 설정할 수 있습니다.",
            ephemeral=True,
        )
        return

    # 데이터베이스에 목표 저장
    success = await bot.db.set_user_goal(
        user_id=interaction.user.id,
        username=interaction.user.display_name,
        weekly_goal=count,
    )

    if success:
        # 현재 주차 정보 가져오기
        week_start, week_end = get_week_start_end()
        week_start_str = week_start.strftime("%m월 %d일")
        week_end_str = week_end.strftime("%m월 %d일")

        embed = discord.Embed(
            title="🎯 운동 목표 설정 완료!",
            description=f"주간 운동 목표가 **{count}회**로 설정되었습니다.",
            color=0x00FF00,
        )
        embed.add_field(
            name="📅 적용 기간",
            value=f"이번 주 ({week_start_str} ~ {week_end_str})",
            inline=False,
        )
        embed.add_field(
            name="💰 벌금 정보",
            value=f"목표 미달성 시 하루당 **{10800//count:,}원**의 벌금이 부과됩니다.",
            inline=False,
        )
        embed.set_footer(text="💪 화이팅! 목표를 달성해보세요!")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"목표 설정 완료: {interaction.user.display_name} - {count}회")
    else:
        await interaction.response.send_message(
            "❌ 목표 설정 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            ephemeral=True,
        )
        logger.error(f"목표 설정 실패: {interaction.user.display_name} - {count}회")


@bot.tree.command(name="get-info", description="이번 주 운동 현황과 벌금을 조회합니다")
async def get_info(interaction: discord.Interaction):
    """운동 현황 조회 슬래시 커맨드"""
    # 사용자 설정 조회
    user_settings = await bot.db.get_user_settings(interaction.user.id)

    if not user_settings:
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

    # 현재 주차 정보
    week_start, week_end = get_week_start_end()
    current_workout_count = await bot.db.get_weekly_workout_count(
        interaction.user.id, week_start
    )

    # 벌금 계산
    weekly_goal = user_settings["weekly_goal"]
    penalty_amount = calculate_penalty(weekly_goal, current_workout_count)
    total_penalty = user_settings["total_penalty"]

    # 진행률 계산
    progress_percentage = min((current_workout_count / weekly_goal) * 100, 100)
    progress_bar = create_progress_bar(current_workout_count, weekly_goal)

    # 상태에 따른 색상 결정
    if current_workout_count >= weekly_goal:
        color = 0x00FF00  # 초록색 (목표 달성)
        status_emoji = "🎉"
        status_text = "목표 달성!"
    elif penalty_amount == 0:
        color = 0x00FF00  # 초록색
        status_emoji = "✅"
        status_text = "벌금 없음"
    elif penalty_amount <= 3000:
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
        description=f"**{status_text}**",
        color=color,
    )

    # 기본 정보
    embed.add_field(name="🎯 이번 주 목표", value=f"{weekly_goal}회", inline=True)
    embed.add_field(
        name="💪 현재 운동 횟수", value=f"{current_workout_count}회", inline=True
    )
    embed.add_field(name="📊 달성률", value=f"{progress_percentage:.1f}%", inline=True)

    # 진행률 바
    embed.add_field(name="📈 진행 상황", value=progress_bar, inline=False)

    # 벌금 정보
    if penalty_amount > 0:
        embed.add_field(
            name="💸 이번 주 예상 벌금",
            value=f"**{format_currency(penalty_amount)}**",
            inline=True,
        )

        remaining_days = 7 - (datetime.now().weekday() + 1)
        if remaining_days > 0:
            embed.add_field(
                name="⏰ 남은 기회",
                value=f"{weekly_goal - current_workout_count}회 ({remaining_days}일 남음)",
                inline=True,
            )
    else:
        embed.add_field(name="💸 이번 주 예상 벌금", value="**0원** 🎉", inline=True)

    embed.add_field(
        name="💰 누적 벌금", value=format_currency(total_penalty), inline=True
    )

    # 주차 정보
    week_start_str = week_start.strftime("%m월 %d일")
    week_end_str = week_end.strftime("%m월 %d일")
    embed.set_footer(text=f"기간: {week_start_str} ~ {week_end_str} | 💪 화이팅!")

    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(
        f"현황 조회: {interaction.user.display_name} - {current_workout_count}/{weekly_goal}회"
    )


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """진행률 바 생성"""
    if total == 0:
        return "📊 " + "▱" * length

    filled = min(int((current / total) * length), length)
    empty = length - filled

    progress = "📊 " + "▰" * filled + "▱" * empty
    progress += f" {current}/{total}"

    return progress


@bot.tree.command(name="revoke", description="잘못된 운동 기록을 취소합니다")
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

    # 대상 사용자의 설정 확인
    user_settings = await bot.db.get_user_settings(member.id)
    if not user_settings:
        await interaction.response.send_message(
            f"❌ {member.display_name}님의 운동 기록이 없습니다.", ephemeral=True
        )
        return

    # 날짜 파싱 (기본값: 오늘)
    if date:
        try:
            from datetime import datetime

            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await interaction.response.send_message(
                "❌ 날짜 형식이 올바르지 않습니다. (예: 2025-06-16)", ephemeral=True
            )
            return
    else:
        target_date = get_today_date()

    # 운동 기록 취소 시도
    success = await bot.db.revoke_workout_record(member.id, target_date)

    if success:
        # 현재 주차 정보 및 운동 횟수 업데이트
        week_start, _ = get_week_start_end()
        current_count = await bot.db.get_weekly_workout_count(member.id, week_start)
        weekly_goal = user_settings["weekly_goal"]

        embed = discord.Embed(
            title="🔄 운동 기록 취소 완료",
            description=f"{member.display_name}님의 {target_date.strftime('%m월 %d일')} 운동 기록이 취소되었습니다.",
            color=0xFF9900,
        )

        # 현재 진행 상황
        progress_bar = create_progress_bar(current_count, weekly_goal)
        embed.add_field(name="📈 현재 진행 상황", value=progress_bar, inline=False)

        # 업데이트된 벌금 정보
        penalty = calculate_penalty(weekly_goal, current_count)
        embed.add_field(
            name="💰 현재 예상 벌금", value=format_currency(penalty), inline=True
        )

        if current_count < weekly_goal:
            remaining = weekly_goal - current_count
            embed.add_field(name="🎯 남은 목표", value=f"{remaining}회", inline=True)

        embed.add_field(
            name="👤 취소 요청자", value=interaction.user.mention, inline=True
        )

        embed.set_footer(text=f"취소된 날짜: {target_date.strftime('%Y년 %m월 %d일')}")

        await interaction.response.send_message(embed=embed)
        logger.info(
            f"운동 기록 취소: {member.display_name} - {target_date.strftime('%Y-%m-%d')} (요청자: {interaction.user.display_name})"
        )

    else:
        embed = discord.Embed(
            title="⚠️ 취소할 기록 없음",
            description=f"{member.display_name}님의 {target_date.strftime('%m월 %d일')} 운동 기록이 없거나 이미 취소되었습니다.",
            color=0xFFFF00,
        )
        embed.add_field(
            name="📅 확인 사항",
            value="• 해당 날짜에 운동 기록이 있는지 확인해주세요\n• 이미 취소된 기록은 다시 취소할 수 없습니다",
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(
            f"운동 기록 취소 실패: {member.display_name} - {target_date.strftime('%Y-%m-%d')} (취소할 기록 없음)"
        )


@bot.event
async def on_message(message):
    """메시지 이벤트 처리"""
    # 봇 자신의 메시지는 무시
    if message.author == bot.user:
        return

    # workout-debugging 채널에서 사진 업로드 감지
    if message.channel.name == WORKOUT_CHANNEL_NAME and message.attachments:
        await handle_workout_photo(message)

    await bot.process_commands(message)


async def handle_workout_photo(message):
    """운동 사진 업로드 처리"""
    user_id = message.author.id
    username = message.author.display_name

    # 사진 파일 확인
    image_found = False
    for attachment in message.attachments:
        if any(
            attachment.filename.lower().endswith(ext)
            for ext in SUPPORTED_IMAGE_EXTENSIONS
        ):
            image_found = True
            break

    if not image_found:
        return

    # 사용자 설정 확인
    user_settings = await bot.db.get_user_settings(user_id)
    if not user_settings:
        embed = discord.Embed(
            title="⚠️ 목표 설정 필요",
            description=f"{message.author.mention}님, 먼저 목표를 설정해주세요!",
            color=0xFFFF00,
        )
        embed.add_field(
            name="📝 설정 방법",
            value="`/set-goals [횟수]` 명령어로 주간 운동 목표를 설정하세요.",
            inline=False,
        )
        await message.reply(embed=embed)
        return

    # 오늘 날짜와 이번 주 시작 날짜
    today = get_today_date()
    week_start, _ = get_week_start_end()

    # 운동 기록 추가 시도
    success = await bot.db.add_workout_record(user_id, username, today, week_start)

    if success:
        # 현재 운동 횟수 조회
        current_count = await bot.db.get_weekly_workout_count(user_id, week_start)
        weekly_goal = user_settings["weekly_goal"]

        # 성공 메시지 생성
        embed = discord.Embed(
            title="💪 운동 기록 완료!",
            description=f"{username}님의 오늘 운동이 기록되었습니다!",
            color=0x00FF00,
        )

        # 진행 상황 추가
        progress_bar = create_progress_bar(current_count, weekly_goal)
        embed.add_field(name="📈 이번 주 진행 상황", value=progress_bar, inline=False)

        # 목표 달성 여부에 따른 메시지
        if current_count >= weekly_goal:
            embed.add_field(
                name="🎉 축하합니다!",
                value="이번 주 목표를 달성하셨습니다!",
                inline=False,
            )
            embed.color = 0xFFD700  # 골드색
        else:
            remaining = weekly_goal - current_count
            embed.add_field(
                name="🎯 남은 목표", value=f"{remaining}회 더 화이팅!", inline=True
            )

            # 현재 예상 벌금
            penalty = calculate_penalty(weekly_goal, current_count)
            embed.add_field(
                name="💰 현재 예상 벌금", value=format_currency(penalty), inline=True
            )

        embed.set_footer(text=f"오늘: {today.strftime('%m월 %d일')}")

        # 반응 추가 및 메시지 전송
        await message.add_reaction("💪")
        await message.reply(embed=embed)

        logger.info(f"운동 기록 성공: {username} - {current_count}/{weekly_goal}회")

    else:
        # 이미 기록된 경우
        embed = discord.Embed(
            title="⚠️ 이미 기록됨",
            description=f"{username}님은 오늘 이미 운동을 기록하셨습니다.",
            color=0xFFFF00,
        )
        embed.add_field(
            name="📅 하루 1회 제한",
            value="하루에 한 번만 운동을 기록할 수 있습니다.",
            inline=False,
        )

        # 현재 진행 상황도 보여주기
        current_count = await bot.db.get_weekly_workout_count(user_id, week_start)
        weekly_goal = user_settings["weekly_goal"]
        progress_bar = create_progress_bar(current_count, weekly_goal)

        embed.add_field(name="📈 현재 진행 상황", value=progress_bar, inline=False)

        await message.add_reaction("⚠️")
        await message.reply(embed=embed)

        logger.info(f"운동 기록 중복: {username} - 오늘 이미 기록됨")


# 메인 실행
async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
