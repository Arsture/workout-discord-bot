"""
Commands Package
슬래시 커맨드들을 기능별로 분리하여 관리합니다.
"""

from .workout_commands import setup_workout_commands
from .admin_commands import setup_admin_commands
from .info_commands import setup_info_commands


def setup_all_commands(bot):
    """모든 슬래시 커맨드를 봇에 등록"""
    setup_workout_commands(bot)
    setup_admin_commands(bot)
    setup_info_commands(bot)


__all__ = [
    "setup_all_commands",
    "setup_workout_commands",
    "setup_admin_commands",
    "setup_info_commands",
]
