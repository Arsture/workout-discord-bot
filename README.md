# Workout Discord Bot

디스코드에서 운동 기록을 관리하고 벌금을 계산하는 봇입니다.

## 주요 기능

- 사진 업로드를 통한 운동 기록 추가
- 주간 운동 목표 설정 및 관리
- 목표 미달성 시 자동 벌금 계산
- 주간 리포트 자동 전송
- 운동 기록 취소 기능
- 관리자 전용 데이터베이스 리셋 기능

## 기술 스택

- **언어**: Python 3.13+
- **프레임워크**: discord.py 2.5.2+
- **데이터베이스**: Supabase (PostgreSQL)
- **스케줄링**: APScheduler
- **배포**: Replit / Railway / Heroku

## 설치 및 설정

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd workout-discord-bot
```

### 2. Poetry 의존성 설치
```bash
poetry install
```

### 3. Supabase 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. SQL Editor에서 다음 테이블들을 생성:

```sql
-- 사용자 설정 테이블
CREATE TABLE user_settings (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    weekly_goal INTEGER NOT NULL DEFAULT 4,
    total_penalty DECIMAL(10,2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 운동 기록 테이블
CREATE TABLE workout_records (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    workout_date DATE NOT NULL,
    week_start_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_revoked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES user_settings (user_id),
    UNIQUE(user_id, workout_date)
);

-- 주간 벌금 기록 테이블
CREATE TABLE weekly_penalties (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    week_start_date DATE NOT NULL,
    goal_count INTEGER NOT NULL,
    actual_count INTEGER NOT NULL,
    penalty_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES user_settings (user_id),
    UNIQUE(user_id, week_start_date)
);
```

### 4. 환경변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Discord Bot 설정
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_guild_id_here

# 채널 설정
WORKOUT_CHANNEL_NAME=workout-debugging
REPORT_CHANNEL_NAME=workout-debugging

# Supabase 설정
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# 주간 리포트 스케줄 설정
REPORT_DAY_OF_WEEK=0  # 0=월요일, 1=화요일, ..., 6=일요일
REPORT_HOUR=0  # 시간 (0-23)
REPORT_MINUTE=0  # 분 (0-59)
REPORT_TIMEZONE=Asia/Seoul  # 시간대

# 관리자 역할 설정
ADMIN_ROLE_NAME=Admin
```

### 5. 봇 실행
```bash
poetry run python main.py
```

## 슬래시 커맨드

- `/set-goals <횟수>`: 주간 운동 목표 설정 (4~7회)
- `/get-info`: 이번 주 운동 현황과 벌금 조회
- `/revoke <사용자> [날짜]`: 운동 기록 취소
- `/weekly-report [주차]`: 주간 리포트 조회
- `/test-report`: 관리자 전용 - 주간 리포트 즉시 전송
- `/reset-db <확인문구>`: 관리자 전용 - 데이터베이스 초기화

## 사용법

1. 봇을 서버에 초대하고 필요한 권한을 부여합니다.
2. `#workout-debugging` 채널을 생성합니다 (또는 환경변수에서 채널명 변경).
3. `/set-goals` 명령어로 개인별 주간 운동 목표를 설정합니다.
4. 운동 후 해당 채널에 사진을 업로드하면 자동으로 기록됩니다.
5. 매주 설정된 시간에 자동으로 벌금 리포트가 전송됩니다.

## 벌금 계산 방식

기본 벌금: **10,080원**

- 주간 목표가 4회인 경우: 부족한 횟수 × 2,520원
- 주간 목표가 5회인 경우: 부족한 횟수 × 2,016원
- 주간 목표가 6회인 경우: 부족한 횟수 × 1,680원
- 주간 목표가 7회인 경우: 부족한 횟수 × 1,440원

## 권한 요구사항

봇이 다음 권한을 가져야 합니다:
- 메시지 보기
- 메시지 보내기
- 슬래시 명령어 사용하기
- 메시지에 반응 추가하기
- 파일 첨부하기

## 개발 정보

- 개발자: arsture
- 버전: 0.1.0
- 라이선스: MIT

## 문제 해결

### 봇이 응답하지 않는 경우
1. Discord Token이 올바른지 확인
2. 봇이 해당 서버에 초대되었는지 확인
3. 봇에 필요한 권한이 부여되었는지 확인

### Supabase 연결 오류
1. SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY가 올바른지 확인
2. Supabase 프로젝트가 활성화되어 있는지 확인
3. 테이블이 올바르게 생성되었는지 확인

### 스케줄된 리포트가 전송되지 않는 경우
1. 시간대 설정 확인 (REPORT_TIMEZONE)
2. 봇이 24/7 실행 중인지 확인
3. 로그에서 에러 메시지 확인
