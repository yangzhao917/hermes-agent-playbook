#!/usr/bin/env python3
"""
每日晨间日程提醒 — cron wrapper script
由 install.py 安装到 ~/.hermes/scripts/morning_reminder.py
"""
import sys
from pathlib import Path

# 共享 lib 在 skills/lib/，与脚本同级的上一级目录的上一级
sys.path.insert(0, str(Path(__file__).parent / "lib"))  # lib: ~/.hermes/scripts/lib/

from cron import get_date_range, lark_calendar_agenda, format_event


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
