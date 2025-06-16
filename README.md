# 워크아웃 Discord 봇

운동을 효율적으로 추적하고 벌금을 계산하는 Discord 봇입니다.

## 기능

1. **운동 목표 설정** (`/set-goals [횟수]`) - 주간 운동 목표 설정 (4~7회)
2. **현황 조회** (`/get-info`) - 이번 주 운동 현황 및 벌금 조회
3. **자동 운동 기록** - 운동 채널에 사진 업로드 시 자동 인식 (하루 1회)
4. **기록 취소** (`/revoke [@멤버] [날짜]`) - 잘못된 운동 기록 취소
5. **주간 리포트 조회** (`/weekly-report [주차]`) - 과거 주간 리포트 개인 조회
6. **자동 주간 리포트** - 설정된 시간에 자동 벌금 현황 전송
7. **리포트 전송** (`/test-report`) - 관리자가 수동으로 리포트 전송

## 벌금 계산 방식

- 기본 벌금: 10,800원
- 일일 벌금: 10,800원 ÷ 목표 운동 횟수
- 주간 벌금: 일일 벌금 × 부족한 운동 횟수

예시: 목표 7회, 실제 3회 → 벌금 = (10,800 ÷ 7) × (7 - 3) = 6,171원

## 설정 방법

### 1. 의존성 설치
```bash
poetry install
```

### 2. 환경변수 설정
`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
# 필수 설정
DISCORD_TOKEN=your_discord_bot_token_here

# 선택적 설정
GUILD_ID=your_guild_id_here
WORKOUT_CHANNEL_NAME=workout-debugging

# 주간 리포트 스케줄 설정
REPORT_DAY_OF_WEEK=0    # 0=월요일, 1=화요일, ..., 6=일요일
REPORT_HOUR=0           # 시간 (0-23)
REPORT_MINUTE=0         # 분 (0-59)
REPORT_TIMEZONE=Asia/Seoul

# 리포트 전송 채널 (기본값: WORKOUT_CHANNEL_NAME과 동일)
REPORT_CHANNEL_NAME=workout-debugging
```

#### 설정 설명:
- `WORKOUT_CHANNEL_NAME`: 운동 사진을 업로드할 채널명
- `REPORT_CHANNEL_NAME`: 주간 리포트를 전송할 채널명
- `REPORT_DAY_OF_WEEK`: 주간 리포트 전송 요일 (0=월요일)
- `REPORT_HOUR/MINUTE`: 주간 리포트 전송 시간
- `REPORT_TIMEZONE`: 시간대 설정

### 3. Discord 봇 생성
1. [Discord Developer Portal](https://discord.com/developers/applications)에서 새 애플리케이션 생성
2. Bot 탭에서 봇 생성 및 토큰 복사
3. 필요한 권한 설정:
   - Send Messages
   - Use Slash Commands
   - Read Message History
   - Add Reactions

### 4. 실행
```bash
poetry run python main.py
```

## 프로젝트 구조

- `main.py` - 메인 봇 파일
- `database.py` - 데이터베이스 관리
- `utils.py` - 유틸리티 함수들
- `config.py` - 설정 상수들
