# 워크아웃 Discord 봇

운동을 효율적으로 추적하고 벌금을 계산하는 Discord 봇입니다.

## 기능

1. **운동 목표 설정** (`/set-goals`) - 주간 운동 목표 설정 (4~7회)
2. **현황 조회** (`/get-info`) - 이번 주 운동 현황 및 벌금 조회
3. **자동 운동 기록** - `workout-debugging` 채널에 사진 업로드 시 자동 인식
4. **기록 취소** (`/revoke`) - 잘못된 운동 기록 취소
5. **주간 리포트** - 매주 월요일 00:00 자동 벌금 현황 전송

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
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_guild_id_here
WORKOUT_CHANNEL_NAME=workout-debugging
```

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
