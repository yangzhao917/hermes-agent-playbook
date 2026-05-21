"""Shared cron wrapper utilities — 供所有 skill 脚本 import"""
import subprocess
import json
from datetime import datetime, timezone, timedelta


def get_cst_now():
    return datetime.now(timezone(timedelta(hours=8)))


def get_date_range(days_offset=0):
    """返回 (date_str, start_iso, end_iso)，CST 时区。"""
    dt = get_cst_now() + timedelta(days=days_offset)
    date_str = dt.strftime("%Y-%m-%d")
    return date_str, f"{date_str}T00:00:00+08:00", f"{date_str}T23:59:59+08:00"


def lark_api(method, path, data=None):
    """调用 lark-cli api，返回解析后的 JSON 或 None。"""
    cmd = ["lark-cli", "api", method, path]
    if data:
        cmd += ["--data", json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def lark_calendar_agenda(start: str, end: str) -> list:
    """调用 lark-cli calendar +agenda，返回事件列表或空列表。"""
    result = subprocess.run(
        ["lark-cli", "calendar", "+agenda",
         "--start", start, "--end", end, "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def format_event_time(start_val: str) -> str:
    """从 ISO 时间字符串提取 HH:MM。"""
    if not start_val:
        return ""
    try:
        dt = datetime.fromisoformat(start_val.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except ValueError:
        return ""


def format_event(ev: dict) -> str:
    """把单个日历事件格式化为 'HH:MM 标题' 或 '标题'。"""
    title = ev.get("summary") or ev.get("title") or "无标题"
    time_str = format_event_time(ev.get("start") or ev.get("start_time") or "")
    return f"{time_str} {title}" if time_str else title
