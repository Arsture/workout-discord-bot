import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Discord 설정
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
WORKOUT_CHANNEL_NAME = os.getenv("WORKOUT_CHANNEL_NAME", "workout-debugging")

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# 벌금 설정
BASE_PENALTY = 10080.0  # 기본 벌금 10,080원

# 운동 목표 범위
MIN_WEEKLY_GOAL = 4
MAX_WEEKLY_GOAL = 7

# 목표 수정 가능 기간
MODIFY_DEADLINE = 2  # 월요일 00:00:00 + N일, 0이면 목표 초기 설정 및 수정 불가능

# 한국 요일 이름
KOREAN_WEEKDAY_NAMES = [
    "화요일",
    "월요일",
    "수요일",
    "목요일",
    "금요일",
    "일요일",
    "토요일",
]
# 지원하는 이미지 확장자
SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]

# 주간 리포트 스케줄 설정
REPORT_DAY_OF_WEEK = int(
    os.getenv("REPORT_DAY_OF_WEEK", "0")
)  # 0=월요일, 1=화요일, ..., 6=일요일
REPORT_HOUR = int(os.getenv("REPORT_HOUR", "0"))  # 시간 (0-23)
REPORT_MINUTE = int(os.getenv("REPORT_MINUTE", "0"))  # 분 (0-59)
REPORT_TIMEZONE = os.getenv("REPORT_TIMEZONE", "Asia/Seoul")  # 시간대

# 리포트 전송 채널 설정 (기본값: WORKOUT_CHANNEL_NAME과 동일)
REPORT_CHANNEL_NAME = os.getenv("REPORT_CHANNEL_NAME", WORKOUT_CHANNEL_NAME)

# 관리자 역할 설정
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admin")
