"""统一的「今天」：本地按系统时间，云端按北京时间。

GitHub Actions 的机器是 UTC，直接在那边用 date.today() 会在北京时间 07:30
拿到「昨天」的日期，所以这里显式指定时区。
"""

from __future__ import annotations

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

DEFAULT_TZ = "Asia/Shanghai"


def today_iso() -> str:
    """返回 YYYY-MM-DD。云端按 Asia/Shanghai，Windows 上没有 tzdata 时退回系统本地时间。"""
    name = os.environ.get("ENGLISH_DAILY_TZ", DEFAULT_TZ)
    try:
        return datetime.now(ZoneInfo(name)).date().isoformat()
    except Exception:
        # Windows 的 Python 默认不带 IANA 时区库，退回本机时间即可（用户本来就在东八区）
        return date.today().isoformat()
