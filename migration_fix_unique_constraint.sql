-- 마이그레이션: UNIQUE 제약조건 수정
-- Supabase SQL Editor에서 실행하세요

-- 1. 기존 UNIQUE 제약조건 제거
ALTER TABLE workout_records DROP CONSTRAINT IF EXISTS workout_records_user_id_workout_date_key;

-- 2. 새로운 부분 UNIQUE 인덱스 생성 (is_revoked=FALSE인 기록만 중복 방지)
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_workout_per_user_date 
ON workout_records(user_id, workout_date) 
WHERE is_revoked = FALSE;

-- 3. 확인 메시지
SELECT 'UNIQUE 제약조건이 성공적으로 수정되었습니다!' as message;

-- 4. 현재 제약조건 확인 (선택사항)
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'workout_records'; 