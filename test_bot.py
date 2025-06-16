#!/usr/bin/env python3
"""
봇 기능 테스트 스크립트
실제 Discord 봇을 실행하기 전에 데이터베이스와 함수들을 테스트할 수 있습니다.
"""

import asyncio
import logging
from datetime import datetime
from database import Database
from utils import calculate_penalty, get_week_start_end, format_currency

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database():
    """데이터베이스 기능 테스트"""
    print("=" * 50)
    print("📁 데이터베이스 기능 테스트")
    print("=" * 50)

    db = Database("test_workout_bot.db")
    await db.init_db()

    # 테스트 사용자 데이터
    test_user_id = 123456789
    test_username = "테스트유저"

    # 1. 목표 설정 테스트
    print("\n1️⃣ 목표 설정 테스트")
    success = await db.set_user_goal(test_user_id, test_username, 5)
    print(f"목표 설정 결과: {'✅ 성공' if success else '❌ 실패'}")

    # 2. 사용자 설정 조회 테스트
    print("\n2️⃣ 사용자 설정 조회 테스트")
    user_settings = await db.get_user_settings(test_user_id)
    if user_settings:
        print(f"사용자: {user_settings['username']}")
        print(f"목표: {user_settings['weekly_goal']}회")
        print(f"누적 벌금: {format_currency(user_settings['total_penalty'])}")
    else:
        print("❌ 사용자 설정을 찾을 수 없습니다")

    # 3. 운동 기록 추가 테스트
    print("\n3️⃣ 운동 기록 추가 테스트")
    week_start, _ = get_week_start_end()
    today = datetime.now()

    # 오늘 운동 기록 추가
    success = await db.add_workout_record(
        test_user_id, test_username, today, week_start
    )
    print(f"운동 기록 추가 결과: {'✅ 성공' if success else '❌ 실패'}")

    # 같은 날 또 추가 시도 (실패해야 함)
    success = await db.add_workout_record(
        test_user_id, test_username, today, week_start
    )
    print(
        f"중복 기록 추가 결과: {'✅ 중복 방지됨' if not success else '❌ 중복 허용됨'}"
    )

    # 4. 주간 운동 횟수 조회 테스트
    print("\n4️⃣ 주간 운동 횟수 조회 테스트")
    workout_count = await db.get_weekly_workout_count(test_user_id, week_start)
    print(f"이번 주 운동 횟수: {workout_count}회")

    # 5. 현황 정보 시뮬레이션 테스트
    print("\n5️⃣ 현황 정보 시뮬레이션 테스트")
    goal = user_settings["weekly_goal"]
    penalty = calculate_penalty(goal, workout_count)
    progress = (workout_count / goal) * 100

    print(f"목표: {goal}회")
    print(f"현재: {workout_count}회")
    print(f"진행률: {progress:.1f}%")
    print(f"예상 벌금: {format_currency(penalty)}")

    # 진행률 바 테스트
    from main import create_progress_bar

    progress_bar = create_progress_bar(workout_count, goal)
    print(f"진행률 바: {progress_bar}")

    # 6. 추가 운동 기록 테스트 (여러 날)
    print("\n6️⃣ 여러 날 운동 기록 테스트")
    from datetime import timedelta

    # 어제 기록 추가
    yesterday = today - timedelta(days=1)
    success = await db.add_workout_record(
        test_user_id, test_username, yesterday, week_start
    )
    print(f"어제 운동 기록: {'✅ 성공' if success else '❌ 실패'}")

    # 내일 기록 추가 (미래 날짜)
    tomorrow = today + timedelta(days=1)
    success = await db.add_workout_record(
        test_user_id, test_username, tomorrow, week_start
    )
    print(f"내일 운동 기록: {'✅ 성공' if success else '❌ 실패'}")

    # 최종 운동 횟수 확인
    final_count = await db.get_weekly_workout_count(test_user_id, week_start)
    print(f"최종 운동 횟수: {final_count}회")

    # 진행률 바 업데이트
    final_progress_bar = create_progress_bar(final_count, goal)
    print(f"최종 진행률 바: {final_progress_bar}")

    # 최종 벌금 계산
    final_penalty = calculate_penalty(goal, final_count)
    print(f"최종 예상 벌금: {format_currency(final_penalty)}")

    # 7. 운동 기록 취소 테스트
    print("\n7️⃣ 운동 기록 취소 테스트")

    # 오늘 기록 취소
    revoke_success = await db.revoke_workout_record(test_user_id, today)
    print(f"오늘 기록 취소: {'✅ 성공' if revoke_success else '❌ 실패'}")

    # 같은 기록 다시 취소 시도 (실패해야 함)
    revoke_again = await db.revoke_workout_record(test_user_id, today)
    print(f"중복 취소 시도: {'❌ 중복 허용됨' if revoke_again else '✅ 중복 방지됨'}")

    # 취소 후 운동 횟수 확인
    after_revoke_count = await db.get_weekly_workout_count(test_user_id, week_start)
    print(f"취소 후 운동 횟수: {after_revoke_count}회")

    # 취소 후 진행률 바
    after_revoke_progress = create_progress_bar(after_revoke_count, goal)
    print(f"취소 후 진행률 바: {after_revoke_progress}")

    # 취소 후 벌금 계산
    after_revoke_penalty = calculate_penalty(goal, after_revoke_count)
    print(f"취소 후 예상 벌금: {format_currency(after_revoke_penalty)}")

    # 8. 주간 리포트 데이터 테스트
    print("\n8️⃣ 주간 리포트 데이터 테스트")

    # 지난 주 데이터 시뮬레이션
    all_users_data = await db.get_all_users_weekly_data(week_start)
    print(f"주간 데이터 조회 결과: {len(all_users_data)}명")

    for user_data in all_users_data:
        weekly_penalty = calculate_penalty(
            user_data["weekly_goal"], user_data["workout_count"]
        )
        print(
            f"- {user_data['username']}: {user_data['workout_count']}/{user_data['weekly_goal']}회 → 벌금 {format_currency(weekly_penalty)}"
        )

        # 주간 벌금 기록 추가
        if weekly_penalty > 0:
            await db.add_weekly_penalty_record(
                user_data["user_id"],
                user_data["username"],
                week_start,
                user_data["weekly_goal"],
                user_data["workout_count"],
                weekly_penalty,
            )
            print(f"  ✅ 주간 벌금 기록 저장됨")

    # 총 벌금 계산
    total_weekly = sum(
        calculate_penalty(u["weekly_goal"], u["workout_count"]) for u in all_users_data
    )
    total_accumulated = sum(u["total_penalty"] for u in all_users_data) + total_weekly
    print(f"총 주간 벌금: {format_currency(total_weekly)}")
    print(f"총 누적 벌금: {format_currency(total_accumulated)}")


def test_utils():
    """유틸리티 함수 테스트"""
    print("\n" + "=" * 50)
    print("🛠️ 유틸리티 함수 테스트")
    print("=" * 50)

    # 1. 벌금 계산 테스트
    print("\n1️⃣ 벌금 계산 테스트")
    test_cases = [
        (7, 7),  # 목표 달성
        (7, 5),  # 2회 부족
        (5, 2),  # 3회 부족
        (4, 0),  # 전혀 안함
    ]

    for goal, actual in test_cases:
        penalty = calculate_penalty(goal, actual)
        print(f"목표 {goal}회, 실제 {actual}회 → 벌금: {format_currency(penalty)}")

    # 2. 주간 날짜 계산 테스트
    print("\n2️⃣ 주간 날짜 계산 테스트")
    week_start, week_end = get_week_start_end()
    print(
        f"이번 주: {week_start.strftime('%Y-%m-%d %H:%M')} ~ {week_end.strftime('%Y-%m-%d %H:%M')}"
    )


async def main():
    """메인 테스트 함수"""
    print("🤖 워크아웃 봇 기능 테스트 시작")

    # 유틸리티 함수 테스트
    test_utils()

    # 데이터베이스 테스트
    await test_database()

    print("\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
