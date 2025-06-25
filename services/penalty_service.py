"""
벌금 계산 서비스
벌금 계산과 관련된 모든 비즈니스 로직을 처리합니다.
"""

from typing import List, Dict
from datetime import datetime
from config import BASE_PENALTY
from models.workout import WeeklyPenalty, WeeklyProgress


class PenaltyService:
    """벌금 계산 서비스"""

    def __init__(self, base_penalty: float = BASE_PENALTY):
        self.base_penalty = base_penalty

    def calculate_penalty(self, goal_count: int, actual_count: int) -> float:
        """
        벌금 계산 함수

        Args:
            goal_count: 목표 운동 횟수
            actual_count: 실제 운동 횟수

        Returns:
            계산된 벌금
        """
        if actual_count >= goal_count:
            return 0.0

        missed_count = goal_count - actual_count
        daily_penalty = self.base_penalty / goal_count
        total_penalty = daily_penalty * missed_count

        return total_penalty

    def calculate_weekly_penalties(self, weekly_data: List[Dict]) -> List[Dict]:
        """
        여러 사용자의 주간 벌금을 일괄 계산

        Args:
            weekly_data: 사용자별 주간 데이터 리스트

        Returns:
            벌금이 계산된 데이터 리스트
        """
        result = []

        for user_data in weekly_data:
            weekly_penalty = self.calculate_penalty(
                user_data["weekly_goal"], user_data["workout_count"]
            )

            result.append(
                {
                    "username": user_data["username"],
                    "user_id": user_data["user_id"],
                    "goal": user_data["weekly_goal"],
                    "actual": user_data["workout_count"],
                    "weekly_penalty": weekly_penalty,
                    "total_penalty": user_data["total_penalty"],
                }
            )

        return result

    def get_penalty_breakdown(
        self, goal_count: int, actual_count: int
    ) -> Dict[str, float]:
        """
        벌금 내역 상세 분석

        Args:
            goal_count: 목표 운동 횟수
            actual_count: 실제 운동 횟수

        Returns:
            벌금 내역 딕셔너리
        """
        if actual_count >= goal_count:
            return {
                "total_penalty": 0.0,
                "daily_penalty": 0.0,
                "missed_days": 0,
                "achievement_rate": 100.0,
            }

        missed_count = goal_count - actual_count
        daily_penalty = self.base_penalty / goal_count
        total_penalty = daily_penalty * missed_count
        achievement_rate = (actual_count / goal_count) * 100

        return {
            "total_penalty": total_penalty,
            "daily_penalty": daily_penalty,
            "missed_days": missed_count,
            "achievement_rate": achievement_rate,
        }

    def estimate_future_penalty(
        self, current_count: int, goal_count: int, remaining_days: int
    ) -> Dict[str, float]:
        """
        미래 벌금 예상치 계산

        Args:
            current_count: 현재 운동 횟수
            goal_count: 목표 운동 횟수
            remaining_days: 남은 일수

        Returns:
            시나리오별 벌금 예상치
        """
        scenarios = {}

        # 현재 상태 유지 시 벌금
        scenarios["current"] = self.calculate_penalty(goal_count, current_count)

        # 목표 달성 시 벌금
        scenarios["best_case"] = 0.0

        # 하루 더 운동할 때마다의 벌금
        for additional_days in range(
            1, min(remaining_days + 1, goal_count - current_count + 1)
        ):
            new_count = current_count + additional_days
            scenarios[f"plus_{additional_days}"] = self.calculate_penalty(
                goal_count, new_count
            )

        return scenarios
