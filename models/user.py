"""
사용자 관련 도메인 모델
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    """디스코드 사용자 정보"""

    user_id: int
    username: str
    display_name: str


@dataclass
class UserSettings:
    """사용자 운동 설정"""

    user_id: int
    username: str
    weekly_goal: int
    total_penalty: float
    created_at: datetime
    updated_at: datetime

    @property
    def is_goal_valid(self) -> bool:
        """목표가 유효한 범위인지 확인"""
        return 4 <= self.weekly_goal <= 7

    def update_goal(self, new_goal: int) -> None:
        """목표 업데이트"""
        if not (4 <= new_goal <= 7):
            raise ValueError("주간 목표는 4-7회 사이여야 합니다.")
        self.weekly_goal = new_goal
        self.updated_at = datetime.now()

    def add_penalty(self, amount: float) -> None:
        """벌금 추가"""
        if amount < 0:
            raise ValueError("벌금은 음수일 수 없습니다.")
        self.total_penalty += amount
