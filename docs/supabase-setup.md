# 🗄️ Supabase 설정 가이드

## Supabase 프로젝트 생성 및 설정

### 1단계: Supabase 계정 생성
1. [Supabase](https://supabase.com) 접속
2. **"Start your project"** 클릭
3. GitHub 계정으로 로그인

### 2단계: 새 프로젝트 생성
1. **"New project"** 버튼 클릭
2. 조직 선택 (개인 계정)
3. 프로젝트 정보 입력:
   - **Name**: `workout-discord-bot`
   - **Database Password**: 강력한 비밀번호 생성
   - **Region**: `Northeast Asia (Seoul)` 선택
4. **"Create new project"** 클릭

### 3단계: 프로젝트 URL 및 키 확인
프로젝트 생성 완료 후:

1. **Settings** → **API** 메뉴 접속
2. 다음 정보 복사:

#### `SUPABASE_URL` 얻기
```
Project URL: https://your-project-id.supabase.co
```
→ 이것이 `SUPABASE_URL`입니다.

#### `SUPABASE_SERVICE_ROLE_KEY` 얻기
```
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
→ 이것이 `SUPABASE_SERVICE_ROLE_KEY`입니다.

⚠️ **중요**: `service_role` 키를 사용하세요. `anon` 키가 아닙니다!

### 4단계: 데이터베이스 테이블 생성

1. **SQL Editor** 메뉴 접속
2. **"New query"** 클릭
3. 다음 SQL을 복사해서 붙여넣기:

```sql
-- 사용자 설정 테이블
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    weekly_goal INTEGER NOT NULL DEFAULT 4,
    total_penalty DECIMAL(10,2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 운동 기록 테이블
CREATE TABLE IF NOT EXISTS workout_records (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    workout_date DATE NOT NULL,
    week_start_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_revoked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES user_settings (user_id) ON DELETE CASCADE,
    UNIQUE(user_id, workout_date)
);

-- 주간 벌금 기록 테이블
CREATE TABLE IF NOT EXISTS weekly_penalties (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    week_start_date DATE NOT NULL,
    weekly_goal INTEGER NOT NULL,
    workout_count INTEGER NOT NULL,
    penalty_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES user_settings (user_id) ON DELETE CASCADE,
    UNIQUE(user_id, week_start_date)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_workout_records_user_week 
ON workout_records (user_id, week_start_date);

CREATE INDEX IF NOT EXISTS idx_workout_records_date 
ON workout_records (workout_date);

CREATE INDEX IF NOT EXISTS idx_weekly_penalties_user_week 
ON weekly_penalties (user_id, week_start_date);
```

4. **"Run"** 버튼 클릭하여 실행

### 5단계: 테이블 생성 확인

1. **Table Editor** 메뉴 접속
2. 다음 테이블들이 생성되었는지 확인:
   - ✅ `user_settings`
   - ✅ `workout_records` 
   - ✅ `weekly_penalties`

### 6단계: Row Level Security (RLS) 설정 (선택사항)

보안을 위해 RLS를 비활성화하거나 적절한 정책을 설정:

```sql
-- RLS 비활성화 (서비스 키 사용 시)
ALTER TABLE user_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE workout_records DISABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_penalties DISABLE ROW LEVEL SECURITY;
```

### 7단계: 연결 테스트

터미널에서 연결 테스트:

```bash
# 환경변수 설정
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Python으로 연결 테스트
python3 -c "
from supabase import create_client
import os
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
result = supabase.table('user_settings').select('*').execute()
print('연결 성공!', result)
"
```

## 🔧 **문제 해결**

### 연결 실패 시 체크리스트
- ✅ `SUPABASE_URL`이 올바른지 확인
- ✅ `service_role` 키를 사용하고 있는지 확인 (`anon` 키 아님)
- ✅ 테이블이 올바르게 생성되었는지 확인
- ✅ RLS 설정이 올바른지 확인

### 자주 발생하는 오류
1. **"relation does not exist"**: 테이블이 생성되지 않음
2. **"insufficient_privilege"**: 잘못된 키 사용
3. **"connection refused"**: URL 오류 