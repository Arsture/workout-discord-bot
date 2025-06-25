"""
운동 관련 도메인 모델
"""

from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass


@dataclass
class WorkoutRecord:
    """운동 기록"""

    id: Optional[int]
    user_id: int
    username: str
    workout_date: date
    week_start_date: date
    created_at: datetime
    is_revoked: bool = False

    @property
    def is_active(self) -> bool:
        """기록이 활성 상태인지 확인"""
        return not self.is_revoked

    def revoke(self) -> None:
        """기록 취소"""
        self.is_revoked = True


@dataclass
class WeeklyPenalty:
    """주간 벌금 기록"""

    id: Optional[int]
    user_id: int
    username: str
    week_start_date: date
    goal_count: int
    actual_count: int
    penalty_amount: float
    created_at: datetime

    @property
    def achievement_rate(self) -> float:
        """달성률 계산"""
        if self.goal_count == 0:
            return 0.0
        return (self.actual_count / self.goal_count) * 100

    @property
    def is_goal_achieved(self) -> bool:
        """목표 달성 여부"""
        return self.actual_count >= self.goal_count


@dataclass
class WeeklyProgress:
    """주간 진행 상황"""

    user_id: int
    username: str
    weekly_goal: int
    current_count: int
    week_start_date: date

    @property
    def remaining_count(self) -> int:
        """남은 운동 횟수"""
        return max(0, self.weekly_goal - self.current_count)

    @property
    def achievement_rate(self) -> float:
        """달성률 계산"""
        if self.weekly_goal == 0:
            return 0.0
        return min((self.current_count / self.weekly_goal) * 100, 100.0)

    @property
    def is_completed(self) -> bool:
        """목표 완료 여부"""
        return self.current_count >= self.weekly_goal
