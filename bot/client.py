"""
워크아웃 디스코드 봇 클라이언트
"""

import logging
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from database import Database
from services import PenaltyService, WorkoutService, ReportService
from config import (
    REPORT_DAY_OF_WEEK,
    REPORT_HOUR,
    REPORT_MINUTE,
    REPORT_TIMEZONE,
)

logger = logging.getLogger(__name__)


class WorkoutBot(commands.Bot):
    """운동 벌금 계산 디스코드 봇"""

    def __init__(self):
        # 봇 인텐트 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True

        super().__init__(command_prefix="!", intents=intents)

        # 의존성 초기화
        self.db = Database()
        self.penalty_service = PenaltyService()
        self.workout_service = WorkoutService(self.db, self.penalty_service)
        self.report_service = ReportService(self.db, self.penalty_service)

        # 스케줄러 초기화
        self.scheduler = AsyncIOScheduler()

    async def setup_hook(self):
        """봇 시작 시 실행되는 설정"""
        try:
            # 데이터베이스 초기화
            await self.db.init_db()
            logger.info("데이터베이스 초기화 완료")

            # 스케줄러 시작
            self.scheduler.start()
            logger.info("스케줄러 시작")

            # 주간 리포트 스케줄 설정
            await self._setup_weekly_report_schedule()

        except Exception as e:
            logger.error(f"봇 설정 중 오류 발생: {e}")
            raise

    async def _setup_weekly_report_schedule(self):
        """주간 리포트 스케줄 설정"""
        try:
            report_tz = pytz.timezone(REPORT_TIMEZONE)
            self.scheduler.add_job(
                self.send_automated_weekly_report,
                CronTrigger(
                    day_of_week=REPORT_DAY_OF_WEEK,
                    hour=REPORT_HOUR,
                    minute=REPORT_MINUTE,
                    timezone=report_tz,
                ),
                id="weekly_report",
            )

            weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
            logger.info(
                f"주간 리포트 스케줄 설정: 매주 {weekday_names[REPORT_DAY_OF_WEEK]}요일 "
                f"{REPORT_HOUR:02d}:{REPORT_MINUTE:02d} ({REPORT_TIMEZONE})"
            )
        except Exception as e:
            logger.error(f"주간 리포트 스케줄 설정 실패: {e}")

    async def on_ready(self):
        """봇이 준비되었을 때"""
        logger.info(f"{self.user}(ID: {self.user.id})로 로그인 완료!")
        logger.info(f"서버 수: {len(self.guilds)}")

        # 슬래시 커맨드 동기화 (로그인 후에만 가능)
        try:
            synced = await self.tree.sync()
            logger.info(f"{len(synced)}개의 슬래시 커맨드 동기화 완료")
        except Exception as e:
            logger.error(f"슬래시 커맨드 동기화 실패: {e}")

        # 현재 등록된 명령어 로그
        commands = [cmd.name for cmd in self.tree.get_commands()]
        logger.info(f"등록된 슬래시 커맨드: {', '.join(commands)}")

    async def send_automated_weekly_report(self):
        """자동 주간 리포트 전송"""
        try:
            logger.info("자동 주간 리포트 생성 시작")

            # 지난 주 데이터로 리포트 생성
            last_week_date = self.report_service.get_last_week_date()

            # 벌금 기록 처리
            penalty_result = await self.report_service.process_weekly_penalty_records(
                last_week_date
            )

            if penalty_result["success"]:
                logger.info(
                    f"벌금 기록 처리 완료: {penalty_result['processed_count']}건, "
                    f"총 {penalty_result['total_penalty_added']}원"
                )

            # 리포트 데이터 생성
            report_data = await self.report_service.generate_weekly_report_data(
                last_week_date
            )

            if not report_data["success"]:
                logger.warning(f"주간 리포트 데이터 없음: {report_data['message']}")
                return

            # 리포트 전송
            await self._send_report_to_channels(report_data)

        except Exception as e:
            logger.error(f"자동 주간 리포트 전송 실패: {e}")

    async def _send_report_to_channels(self, report_data: dict):
        """채널에 리포트 전송"""
        from config import REPORT_CHANNEL_NAME

        embed = self.report_service.create_weekly_report_embed(report_data)

        # 모든 길드에서 리포트 채널 찾기
        sent_count = 0
        for guild in self.guilds:
            target_channel = None

            # 설정된 리포트 채널 찾기
            for channel in guild.text_channels:
                if channel.name == REPORT_CHANNEL_NAME:
                    target_channel = channel
                    break

            # 리포트 채널이 없으면 첫 번째 텍스트 채널 사용
            if not target_channel:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        target_channel = channel
                        break

            if target_channel:
                try:
                    await target_channel.send(embed=embed)
                    sent_count += 1
                    logger.info(
                        f"리포트 전송 완료: {guild.name} #{target_channel.name}"
                    )
                except discord.Forbidden:
                    logger.warning(
                        f"리포트 전송 권한 없음: {guild.name} #{target_channel.name}"
                    )
                except Exception as e:
                    logger.error(f"리포트 전송 실패: {guild.name} - {e}")

        logger.info(f"총 {sent_count}개 채널에 주간 리포트 전송 완료")

    async def close(self):
        """봇 종료 시 정리 작업"""
        if hasattr(self, "scheduler") and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("스케줄러 종료")

        await super().close()
        logger.info("봇 종료 완료")
