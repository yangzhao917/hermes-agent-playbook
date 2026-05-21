#!/usr/bin/env python3
"""
每日晨间日程提醒 — cron wrapper script
由 install.py 安装到 ~/.hermes/scripts/morning_reminder.py
"""
import subprocess
import json
import sys
from datetime import datetime, timezone, timedelta

def get_today_range():
    now = datetime.now(timezone(timedelta(hours=8)))
    date_str = now.strftime("%Y-%m-%d")
    return date_str, f"{date_str}T00:00:00+08:00", f"{date_str}T23:59:59+08:00"

def get_tomorrow_range():
    now = datetime.now(timezone(timedelta(hours=8))) + timedelta(days=1)
    date_str = now.strftime("%Y-%m-%d")
    return date_str, f"{date_str}T00:00:00+08:00", f"{date_str}T23:59:59+08:00"

def query_calendar(start: str, end: str) -> list:
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

def format_events(events: list) -> str:
    if not events:
        return "暂无安排 🎉"
    lines = []
    for ev in events:
        title = ev.get("summary") or ev.get("title") or "无标题"
        start_val = ev.get("start") or ev.get("start_time") or ""
        time_str = ""
        if start_val:
            try:
                dt = datetime.fromisoformat(start_val.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except ValueError:
                time_str = ""
        if time_str:
            lines.append(f"{time_str} {title}")
        else:
            lines.append(title)
    return "\n".join(lines)

today_str, today_start, today_end = get_today_range()
tomorrow_str, tomorrow_start, tomorrow_end = get_tomorrow_range()

today_ev = query_calendar(today_start, today_end)
tomorrow_ev = query_calendar(tomorrow_start, tomorrow_end)

print("☀️ 今日日程")
print(format_events(today_ev))
print()
print("📅 明日日程（你可能更关心这个）")
print(format_events(tomorrow_ev))
