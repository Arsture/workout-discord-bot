import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "workout_bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """데이터베이스 테이블 초기화"""
        async with aiosqlite.connect(self.db_path) as db:
            # 사용자 설정 테이블
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    weekly_goal INTEGER NOT NULL DEFAULT 4,
                    total_penalty REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 운동 기록 테이블
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS workout_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    workout_date DATE NOT NULL,
                    week_start_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_revoked BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES user_settings (user_id),
                    UNIQUE(user_id, workout_date)
                )
            """
            )

            # 주간 벌금 기록 테이블
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS weekly_penalties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    week_start_date DATE NOT NULL,
                    goal_count INTEGER NOT NULL,
                    actual_count INTEGER NOT NULL,
                    penalty_amount REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_settings (user_id),
                    UNIQUE(user_id, week_start_date)
                )
            """
            )

            await db.commit()
            logger.info("데이터베이스 테이블 초기화 완료")

    async def set_user_goal(
        self, user_id: int, username: str, weekly_goal: int
    ) -> bool:
        """사용자의 주간 운동 목표 설정"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO user_settings 
                    (user_id, username, weekly_goal, total_penalty, updated_at)
                    VALUES (?, ?, ?, 
                            COALESCE((SELECT total_penalty FROM user_settings WHERE user_id = ?), 0),
                            ?)
                """,
                    (user_id, username, weekly_goal, user_id, datetime.now()),
                )
                await db.commit()
                logger.info(
                    f"사용자 {username}(ID: {user_id})의 목표를 {weekly_goal}회로 설정"
                )
                return True
        except Exception as e:
            logger.error(f"목표 설정 실패: {e}")
            return False

    async def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """사용자 설정 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    """
                    SELECT user_id, username, weekly_goal, total_penalty, created_at, updated_at
                    FROM user_settings WHERE user_id = ?
                """,
                    (user_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "user_id": row[0],
                            "username": row[1],
                            "weekly_goal": row[2],
                            "total_penalty": row[3],
                            "created_at": row[4],
                            "updated_at": row[5],
                        }
                    return None
        except Exception as e:
            logger.error(f"사용자 설정 조회 실패: {e}")
            return None

    async def add_workout_record(
        self,
        user_id: int,
        username: str,
        workout_date: datetime,
        week_start_date: datetime,
    ) -> bool:
        """운동 기록 추가 (하루 1회 제한)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR IGNORE INTO workout_records 
                    (user_id, username, workout_date, week_start_date)
                    VALUES (?, ?, ?, ?)
                """,
                    (user_id, username, workout_date.date(), week_start_date.date()),
                )

                # 실제로 삽입되었는지 확인
                if db.total_changes > 0:
                    await db.commit()
                    logger.info(f"운동 기록 추가: {username} - {workout_date.date()}")
                    return True
                else:
                    logger.info(f"이미 기록된 운동: {username} - {workout_date.date()}")
                    return False
        except Exception as e:
            logger.error(f"운동 기록 추가 실패: {e}")
            return False

    async def revoke_workout_record(self, user_id: int, workout_date: datetime) -> bool:
        """운동 기록 취소"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    UPDATE workout_records 
                    SET is_revoked = TRUE 
                    WHERE user_id = ? AND workout_date = ? AND is_revoked = FALSE
                """,
                    (user_id, workout_date.date()),
                )

                if db.total_changes > 0:
                    await db.commit()
                    logger.info(
                        f"운동 기록 취소: 사용자 {user_id} - {workout_date.date()}"
                    )
                    return True
                else:
                    logger.info(
                        f"취소할 운동 기록 없음: 사용자 {user_id} - {workout_date.date()}"
                    )
                    return False
        except Exception as e:
            logger.error(f"운동 기록 취소 실패: {e}")
            return False

    async def get_weekly_workout_count(
        self, user_id: int, week_start_date: datetime
    ) -> int:
        """특정 주의 운동 횟수 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    """
                    SELECT COUNT(*) FROM workout_records 
                    WHERE user_id = ? AND week_start_date = ? AND is_revoked = FALSE
                """,
                    (user_id, week_start_date.date()),
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
        except Exception as e:
            logger.error(f"주간 운동 횟수 조회 실패: {e}")
            return 0

    async def get_all_users_weekly_data(self, week_start_date: datetime) -> List[Dict]:
        """모든 사용자의 주간 데이터 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    """
                    SELECT 
                        us.user_id,
                        us.username,
                        us.weekly_goal,
                        us.total_penalty,
                        COALESCE(wr.workout_count, 0) as workout_count
                    FROM user_settings us
                    LEFT JOIN (
                        SELECT user_id, COUNT(*) as workout_count
                        FROM workout_records 
                        WHERE week_start_date = ? AND is_revoked = FALSE
                        GROUP BY user_id
                    ) wr ON us.user_id = wr.user_id
                """,
                    (week_start_date.date(),),
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        {
                            "user_id": row[0],
                            "username": row[1],
                            "weekly_goal": row[2],
                            "total_penalty": row[3],
                            "workout_count": row[4],
                        }
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"전체 사용자 주간 데이터 조회 실패: {e}")
            return []

    async def add_weekly_penalty_record(
        self,
        user_id: int,
        username: str,
        week_start_date: datetime,
        goal_count: int,
        actual_count: int,
        penalty_amount: float,
    ) -> bool:
        """주간 벌금 기록 추가 및 누적 벌금 업데이트 (트랜잭션)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 1. 주간 벌금 기록 (이미 있으면 무시)
                await db.execute(
                    """
                    INSERT OR IGNORE INTO weekly_penalties
                    (user_id, username, week_start_date, goal_count, actual_count, penalty_amount, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        username,
                        week_start_date.date(),
                        goal_count,
                        actual_count,
                        penalty_amount,
                        datetime.now(),
                    ),
                )

                # 2. 실제로 새로운 기록이 추가되었는지 확인
                if db.total_changes > 0:
                    # 3. 누적 벌금 업데이트
                    await db.execute(
                        """
                        UPDATE user_settings
                        SET total_penalty = total_penalty + ?, updated_at = ?
                        WHERE user_id = ?
                    """,
                        (penalty_amount, datetime.now(), user_id),
                    )
                    await db.commit()
                    logger.info(
                        f"주간 벌금 기록 및 누적 벌금 업데이트 완료: {username} (+{penalty_amount}원)"
                    )
                    return True
                else:
                    logger.info(
                        f"이미 처리된 주간 벌금: {username} - {week_start_date.date()}"
                    )
                    return False
        except Exception as e:
            logger.error(f"주간 벌금 처리 실패: {e}")
            return False

    async def get_total_accumulated_penalty(self) -> float:
        """모든 사용자의 전체 누적 벌금 합계 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT SUM(total_penalty) FROM user_settings"
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row and row[0] is not None else 0.0
        except Exception as e:
            logger.error(f"전체 누적 벌금 합계 조회 실패: {e}")
            return 0.0
