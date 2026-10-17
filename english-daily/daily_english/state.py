"""进度状态：记住轮到第几句、上次推送日期，避免同一天重复推送。

云端（GitHub Actions）每次都是全新的工作目录，读不到本地状态，
所以云端用 run.py --by-date 直接按日期算轮换，不依赖这个文件。
"""

from __future__ import annotations

import json
from pathlib import Path

from .clock import today_iso

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "state.json"


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # 状态文件坏了不该影响推送，当作全新开始即可
        return {}


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def choose_index(total: int, force_new: bool = False, today: str | None = None) -> int:
    """决定今天用第几句（0 起始）。

    规则：
    - 同一天重复运行，返回同一句（幂等），除非 force_new=True；
    - 换了一天就往后轮换一句，全部用过一轮后自动从头循环。
    """
    today = today or today_iso()
    state = _read(STATE_PATH)

    if not force_new and state.get("last_date") == today and "last_index" in state:
        last = int(state["last_index"])
        if 0 <= last < total:
            return last

    cursor = int(state.get("cursor", 0)) % total
    state["cursor"] = (cursor + 1) % total
    state["last_index"] = cursor
    state["last_date"] = today
    history = state.get("history", [])
    history.append({"date": today, "index": cursor})
    state["history"] = history[-90:]
    _write(STATE_PATH, state)
    return cursor


def index_for_date(total: int, day: str) -> int:
    """纯按日期算轮换位置：同一天永远同一句，跨天自动往后走，不需要任何状态文件。

    GitHub Actions 用这个：每次都是干净环境，没法记住上次跑到哪。
    """
    from datetime import date

    return date.fromisoformat(day).toordinal() % total


def peek_state() -> dict:
    return _read(STATE_PATH)


def pushed_today(day: str | None = None) -> bool:
    """今天是否已经成功推送过（用于「开机登录也触发一次」时去重）。"""
    day = day or today_iso()
    state = _read(STATE_PATH)
    return day in state.get("pushed_dates", [])


def mark_pushed(day: str | None = None) -> None:
    """记录某天已经推送成功。只保留最近 60 天。"""
    day = day or today_iso()
    state = _read(STATE_PATH)
    dates = [d for d in state.get("pushed_dates", []) if d != day]
    dates.append(day)
    state["pushed_dates"] = dates[-60:]
    _write(STATE_PATH, state)
