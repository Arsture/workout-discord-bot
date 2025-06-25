import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        """Supabase 클라이언트 초기화"""
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("Supabase URL과 Service Role Key가 필요합니다.")

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase 클라이언트 초기화 완료")

    async def init_db(self):
        """데이터베이스 테이블 확인 및 초기화"""
        try:
            # 테이블이 이미 존재하는지 확인 (스키마 체크)
            # Supabase에서는 테이블을 웹 인터페이스나 SQL 에디터에서 미리 생성해야 합니다.
            # 여기서는 연결만 확인합니다.
            response = (
                self.supabase.table("user_settings")
                .select("count", count="exact")
                .limit(1)
                .execute()
            )
            logger.info("Supabase 데이터베이스 연결 확인 완료")
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise

    async def set_user_goal(
        self, user_id: int, username: str, weekly_goal: int
    ) -> bool:
        """사용자의 주간 운동 목표 설정"""
        try:
            # 기존 사용자 확인
            existing_user = (
                self.supabase.table("user_settings")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if existing_user.data:
                # 기존 사용자 업데이트
                response = (
                    self.supabase.table("user_settings")
                    .update(
                        {
                            "username": username,
                            "weekly_goal": weekly_goal,
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
                    .eq("user_id", user_id)
                    .execute()
                )
            else:
                # 새 사용자 생성
                response = (
                    self.supabase.table("user_settings")
                    .insert(
                        {
                            "user_id": user_id,
                            "username": username,
                            "weekly_goal": weekly_goal,
                            "total_penalty": 0.0,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
                    .execute()
                )

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
            response = (
                self.supabase.table("user_settings")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                return response.data[0]
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
            workout_date_str = workout_date.date().isoformat()
            week_start_str = week_start_date.date().isoformat()

            # 이미 해당 날짜에 기록이 있는지 확인 (취소되지 않은 기록만)
            existing_record = (
                self.supabase.table("workout_records")
                .select("id, is_revoked")
                .eq("user_id", user_id)
                .eq("workout_date", workout_date_str)
                .eq("is_revoked", False)
                .execute()
            )

            if existing_record.data:
                logger.info(
                    f"이미 기록된 운동 (취소되지 않음): {username} - {workout_date_str}"
                )
                return False

            # 새 운동 기록 추가
            response = (
                self.supabase.table("workout_records")
                .insert(
                    {
                        "user_id": user_id,
                        "username": username,
                        "workout_date": workout_date_str,
                        "week_start_date": week_start_str,
                        "created_at": datetime.now().isoformat(),
                        "is_revoked": False,
                    }
                )
                .execute()
            )

            if response.data:
                logger.info(
                    f"운동 기록 추가 성공: {username} - {workout_date_str} - ID: {response.data[0].get('id')}"
                )
                return True
            else:
                logger.error(
                    f"운동 기록 추가 실패 (응답 데이터 없음): {username} - {workout_date_str}"
                )
                return False
        except Exception as e:
            logger.error(f"운동 기록 추가 실패: {e}")
            return False

    async def revoke_workout_record(self, user_id: int, workout_date: datetime) -> bool:
        """운동 기록 취소"""
        try:
            workout_date_str = workout_date.date().isoformat()

            # 취소할 기록 확인 (취소되지 않은 기록만)
            existing_record = (
                self.supabase.table("workout_records")
                .select("id, is_revoked, created_at")
                .eq("user_id", user_id)
                .eq("workout_date", workout_date_str)
                .eq("is_revoked", False)
                .execute()
            )

            if not existing_record.data:
                # 추가 디버깅: 해당 날짜의 모든 기록 확인
                all_records = (
                    self.supabase.table("workout_records")
                    .select("id, is_revoked, created_at")
                    .eq("user_id", user_id)
                    .eq("workout_date", workout_date_str)
                    .execute()
                )

                if all_records.data:
                    logger.info(
                        f"취소할 운동 기록 없음 (이미 취소된 기록 존재): 사용자 {user_id} - {workout_date_str} - 기록 수: {len(all_records.data)}"
                    )
                else:
                    logger.info(
                        f"취소할 운동 기록 없음 (기록 자체가 없음): 사용자 {user_id} - {workout_date_str}"
                    )
                return False

            # 기록 취소 (is_revoked를 True로 설정)
            response = (
                self.supabase.table("workout_records")
                .update({"is_revoked": True})
                .eq("user_id", user_id)
                .eq("workout_date", workout_date_str)
                .eq("is_revoked", False)  # 이미 취소된 기록은 다시 취소할 수 없음
                .execute()
            )

            # 실제로 업데이트된 행이 있는지 확인
            if not response.data:
                logger.info(
                    f"취소할 운동 기록 없음 (이미 취소됨): 사용자 {user_id} - {workout_date_str}"
                )
                return False

            logger.info(f"운동 기록 취소: 사용자 {user_id} - {workout_date_str}")
            return True
        except Exception as e:
            logger.error(f"운동 기록 취소 실패: {e}")
            return False

    async def get_weekly_workout_count(
        self, user_id: int, week_start_date: datetime
    ) -> int:
        """특정 주의 운동 횟수 조회"""
        try:
            week_start_str = week_start_date.date().isoformat()

            response = (
                self.supabase.table("workout_records")
                .select("*", count="exact")
                .eq("user_id", user_id)
                .eq("week_start_date", week_start_str)
                .eq("is_revoked", False)
                .execute()
            )

            return response.count if response.count else 0
        except Exception as e:
            logger.error(f"주간 운동 횟수 조회 실패: {e}")
            return 0

    async def get_all_users_weekly_data(self, week_start_date: datetime) -> List[Dict]:
        """모든 사용자의 주간 데이터 조회"""
        try:
            week_start_str = week_start_date.date().isoformat()

            # 모든 사용자 설정 가져오기
            users_response = self.supabase.table("user_settings").select("*").execute()

            if not users_response.data:
                return []

            result = []
            for user in users_response.data:
                user_id = user["user_id"]

                # 해당 주의 운동 횟수 조회
                workout_count_response = (
                    self.supabase.table("workout_records")
                    .select("*", count="exact")
                    .eq("user_id", user_id)
                    .eq("week_start_date", week_start_str)
                    .eq("is_revoked", False)
                    .execute()
                )

                workout_count = (
                    workout_count_response.count if workout_count_response.count else 0
                )

                result.append(
                    {
                        "user_id": user_id,
                        "username": user["username"],
                        "weekly_goal": user["weekly_goal"],
                        "workout_count": workout_count,
                        "total_penalty": user["total_penalty"],
                    }
                )

            return result
        except Exception as e:
            logger.error(f"모든 사용자 주간 데이터 조회 실패: {e}")
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
        """주간 벌금 기록 추가 (중복 방지)"""
        try:
            week_start_str = week_start_date.date().isoformat()

            # 이미 해당 주에 벌금 기록이 있는지 확인
            existing_penalty = (
                self.supabase.table("weekly_penalties")
                .select("*")
                .eq("user_id", user_id)
                .eq("week_start_date", week_start_str)
                .execute()
            )

            if existing_penalty.data:
                logger.info(f"이미 벌금 기록 존재: {username} - {week_start_str}")
                return False

            # 새 벌금 기록 추가
            penalty_response = (
                self.supabase.table("weekly_penalties")
                .insert(
                    {
                        "user_id": user_id,
                        "username": username,
                        "week_start_date": week_start_str,
                        "goal_count": goal_count,
                        "actual_count": actual_count,
                        "penalty_amount": penalty_amount,
                        "created_at": datetime.now().isoformat(),
                    }
                )
                .execute()
            )

            # 사용자의 총 벌금 업데이트
            user_settings = await self.get_user_settings(user_id)
            if user_settings:
                new_total_penalty = user_settings["total_penalty"] + penalty_amount
                update_response = (
                    self.supabase.table("user_settings")
                    .update(
                        {
                            "total_penalty": new_total_penalty,
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
                    .eq("user_id", user_id)
                    .execute()
                )

            logger.info(f"주간 벌금 기록 추가: {username} - {penalty_amount}원")
            return True
        except Exception as e:
            logger.error(f"주간 벌금 기록 추가 실패: {e}")
            return False

    async def get_total_accumulated_penalty(self) -> float:
        """전체 누적 벌금 조회"""
        try:
            response = (
                self.supabase.table("user_settings").select("total_penalty").execute()
            )

            if response.data:
                total_penalty = sum(user["total_penalty"] for user in response.data)
                return total_penalty
            return 0.0
        except Exception as e:
            logger.error(f"전체 누적 벌금 조회 실패: {e}")
            return 0.0

    async def reset_database(self) -> bool:
        """데이터베이스 초기화 (모든 데이터 삭제)"""
        try:
            # 테이블 순서대로 데이터 삭제
            # 먼저 외래키 참조가 있는 테이블부터 삭제

            # 1. weekly_penalties 테이블 모든 데이터 삭제
            self.supabase.table("weekly_penalties").delete().neq("id", 0).execute()

            # 2. workout_records 테이블 모든 데이터 삭제
            self.supabase.table("workout_records").delete().neq("id", 0).execute()

            # 3. user_settings 테이블 모든 데이터 삭제
            self.supabase.table("user_settings").delete().neq("user_id", 0).execute()

            logger.warning("데이터베이스가 완전히 초기화되었습니다")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            return False
