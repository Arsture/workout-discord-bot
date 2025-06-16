import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Discord 설정
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
WORKOUT_CHANNEL_NAME = os.getenv("WORKOUT_CHANNEL_NAME", "workout-debugging")

# 벌금 설정
BASE_PENALTY = 10800.0  # 기본 벌금 10,800원

# 운동 목표 범위
MIN_WEEKLY_GOAL = 4
MAX_WEEKLY_GOAL = 7

# 데이터베이스 설정
DATABASE_PATH = "workout_bot.db"

# 지원하는 이미지 확장자
SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]
