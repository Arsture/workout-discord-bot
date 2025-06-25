"""
대안 해결책: UPSERT를 사용한 add_workout_record 메서드

이 방법은 데이터베이스 스키마를 수정하지 않고
코드 레벨에서 UNIQUE 제약조건 문제를 해결합니다.
"""


async def add_workout_record_upsert(
    self,
    user_id: int,
    username: str,
    workout_date: datetime,
    week_start_date: datetime,
) -> bool:
    """
    운동 기록 추가 (UPSERT 방식)

    기존 기록이 있으면:
    - is_revoked=True이면 is_revoked=False로 업데이트
    - is_revoked=False이면 중복으로 간주하여 False 반환

    기존 기록이 없으면:
    - 새로운 기록 추가
    """
    try:
        workout_date_str = workout_date.date().isoformat()
        week_start_str = week_start_date.date().isoformat()

        # 1. 기존 기록 확인 (모든 기록)
        existing_record = (
            self.supabase.table("workout_records")
            .select("id, is_revoked")
            .eq("user_id", user_id)
            .eq("workout_date", workout_date_str)
            .execute()
        )

        if existing_record.data:
            record = existing_record.data[0]

            if record["is_revoked"]:
                # 이미 취소된 기록이 있으면 다시 활성화
                response = (
                    self.supabase.table("workout_records")
                    .update(
                        {
                            "is_revoked": False,
                            "username": username,  # 최신 사용자명으로 업데이트
                            "week_start_date": week_start_str,
                            "created_at": datetime.now().isoformat(),
                        }
                    )
                    .eq("id", record["id"])
                    .execute()
                )

                if response.data:
                    logger.info(f"운동 기록 재활성화: {username} - {workout_date_str}")
                    return True
                else:
                    logger.error(
                        f"운동 기록 재활성화 실패: {username} - {workout_date_str}"
                    )
                    return False
            else:
                # 이미 활성 기록이 있음
                logger.info(f"이미 기록된 운동 (활성): {username} - {workout_date_str}")
                return False
        else:
            # 기존 기록이 없으면 새로 추가
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
                logger.info(f"운동 기록 추가 성공: {username} - {workout_date_str}")
                return True
            else:
                logger.error(f"운동 기록 추가 실패: {username} - {workout_date_str}")
                return False

    except Exception as e:
        logger.error(f"운동 기록 UPSERT 실패: {e}")
        return False


# 사용법:
# database.py에서 기존 add_workout_record 메서드를 위의 코드로 교체하거나
# 새로운 메서드로 추가한 후 workout_service.py에서 호출 변경
