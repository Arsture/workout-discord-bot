"""
Domain Models
운동 봇의 핵심 도메인 모델들을 정의합니다.
"""

from .user import User, UserSettings
from .workout import WorkoutRecord, WeeklyPenalty, WeeklyProgress

__all__ = ["User", "UserSettings", "WorkoutRecord", "WeeklyPenalty", "WeeklyProgress"]
