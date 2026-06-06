"""
周次计算工具。

为什么单独抽出来：dictation_repo 和 checkin_repo 都需要计算 year_week，
放在 services 层作为纯计算工具，避免两处重复实现。
"""
from datetime import datetime


def get_year_week(dt: datetime) -> str:
    """
    将 datetime 转换为 YYYYWW 格式的周次字符串。

    为什么用 ISO week number：ISO 周从周一开始，跨年边界处理更标准，
    isocalendar() 是 Python 内置方法无需额外依赖。

    示例：2026-06-01 -> '202623'
    """
    iso = dt.isocalendar()  # 返回 (year, week, weekday)
    # 补零确保周次始终两位数，如第 3 周 -> '03'
    return f"{iso[0]}{iso[1]:02d}"
