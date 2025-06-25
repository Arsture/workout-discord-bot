"""
운동 벌금 계산 디스코드 봇 - Clean Architecture 버전
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from bot.client import WorkoutBot
from bot.events import EventHandler
from commands import setup_all_commands
from config import DISCORD_TOKEN

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 웹 서버 설정 (Keep-alive용)
app = Flask(__name__)


@app.route("/")
def home():
    return "Workout Discord Bot is running!"


def run_web_server():
    """웹 서버 실행 (백그라운드)"""
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)


def start_web_server_in_thread():
    """별도 스레드에서 웹 서버 시작"""
    server_thread = Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logger.info("웹 서버가 백그라운드에서 시작되었습니다 (포트: 8080)")


async def main():
    """메인 실행 함수"""
    try:
        # 웹 서버 시작
        start_web_server_in_thread()

        # 디스코드 토큰 확인
        if not DISCORD_TOKEN:
            logger.error("DISCORD_TOKEN이 설정되지 않았습니다!")
            return

        # 봇 인스턴스 생성
        bot = WorkoutBot()

        # 이벤트 핸들러 등록
        event_handler = EventHandler(bot)
        event_handler.register_events()

        # 슬래시 커맨드 등록
        setup_all_commands(bot)

        # 슬래시 커맨드 동기화
        await bot.sync_commands()

        logger.info("봇 시작 중...")

        # 봇 실행
        async with bot:
            await bot.start(DISCORD_TOKEN)

    except KeyboardInterrupt:
        logger.info("봇 종료 요청 받음")
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {e}")
        raise
    finally:
        logger.info("봇이 안전하게 종료되었습니다")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n봇을 종료합니다...")
    except Exception as e:
        logger.error(f"프로그램 실행 중 치명적 오류: {e}")
        exit(1)
