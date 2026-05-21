#!/usr/bin/env python3
"""
每日晨间日程提醒
Queries Feishu calendar for today and tomorrow, prints formatted agenda.
"""
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


def format_event(ev: dict) -> str:
    """把单个日历事件格式化为 'HH:MM 标题' 或 '标题'。"""
    title = ev.get("summary") or ev.get("title") or "无标题"
    start_val = ev.get("start") or ev.get("start_time") or ""
    time_str = ""
    if start_val:
        try:
            dt = datetime.fromisoformat(start_val.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M")
        except ValueError:
            pass
    return f"{time_str} {title}" if time_str else title


def main():
    today_str, today_start, today_end = get_date_range(0)
    tomorrow_str, tomorrow_start, tomorrow_end = get_date_range(1)

    today_ev = lark_calendar_agenda(today_start, today_end)
    tomorrow_ev = lark_calendar_agenda(tomorrow_start, tomorrow_end)

    print("☀️ 今日日程")
    if not today_ev:
        print("  暂无安排 🎉")
    else:
        for ev in today_ev:
            print(f"  {format_event(ev)}")

    print()
    print("📅 明日日程（你可能更关心这个）")
    if not tomorrow_ev:
        print("  暂无安排 🎉")
    else:
        for ev in tomorrow_ev:
            print(f"  {format_event(ev)}")


if __name__ == "__main__":
    main()
