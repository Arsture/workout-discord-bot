-- Workout Discord Bot - Supabase Schema
-- 이 파일을 Supabase SQL Editor에서 실행하여 테이블을 생성하세요.

-- 1. 사용자 설정 테이블
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    weekly_goal INTEGER NOT NULL DEFAULT 4,
    total_penalty DECIMAL(10,2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 운동 기록 테이블
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

-- 3. 주간 벌금 기록 테이블
CREATE TABLE IF NOT EXISTS weekly_penalties (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    week_start_date DATE NOT NULL,
    goal_count INTEGER NOT NULL,
    actual_count INTEGER NOT NULL,
    penalty_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES user_settings (user_id) ON DELETE CASCADE,
    UNIQUE(user_id, week_start_date)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_workout_records_user_week ON workout_records(user_id, week_start_date);
CREATE INDEX IF NOT EXISTS idx_workout_records_date ON workout_records(workout_date);
CREATE INDEX IF NOT EXISTS idx_weekly_penalties_user_week ON weekly_penalties(user_id, week_start_date);

-- Row Level Security 활성화 (선택사항)
-- ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE workout_records ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE weekly_penalties ENABLE ROW LEVEL SECURITY;

-- RLS 정책 생성 예시 (필요시 수정하여 사용)
-- CREATE POLICY "Enable read access for service role" ON user_settings
--     FOR SELECT USING (true);
-- CREATE POLICY "Enable insert access for service role" ON user_settings
--     FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Enable update access for service role" ON user_settings
--     FOR UPDATE USING (true);
-- CREATE POLICY "Enable delete access for service role" ON user_settings
--     FOR DELETE USING (true);

-- 테이블 생성 완료 메시지
SELECT 'Workout Discord Bot 테이블들이 성공적으로 생성되었습니다!' as message; 