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
from utils import calculate_penalty, get_week_start_end
from config import MIN_WEEKLY_GOAL, MAX_WEEKLY_GOAL

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
    # TODO: 구현 예정
    await interaction.response.send_message(
        "현황 조회 기능 (구현 예정)", ephemeral=True
    )


@bot.tree.command(name="revoke", description="잘못된 운동 기록을 취소합니다")
async def revoke(interaction: discord.Interaction, member: discord.Member):
    """운동 기록 취소 슬래시 커맨드"""
    # TODO: 구현 예정
    await interaction.response.send_message(
        f"{member.mention}의 운동 기록 취소 기능 (구현 예정)", ephemeral=True
    )


@bot.event
async def on_message(message):
    """메시지 이벤트 처리"""
    # 봇 자신의 메시지는 무시
    if message.author == bot.user:
        return

    # workout-debugging 채널에서 사진 업로드 감지
    if message.channel.name == "workout-debugging" and message.attachments:
        for attachment in message.attachments:
            if any(
                attachment.filename.lower().endswith(ext)
                for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
            ):
                # TODO: 운동 기록 저장 로직 구현
                await message.add_reaction("💪")
                logger.info(f"{message.author.name}이 운동 사진을 업로드했습니다.")
                break

    await bot.process_commands(message)


# 메인 실행
async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
