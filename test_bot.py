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
