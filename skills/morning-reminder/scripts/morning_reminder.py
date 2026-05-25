#!/usr/bin/env python3
"""
morning-reminder: 每日晨间日程提醒
- 今日日程（时间线）
- 今日待办（截止≤今天，含逾期预警）
- 明日日程（前3条+总数）
"""

import subprocess
import json
import re
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CAL_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py"
TASK_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-task/scripts/list_tasks.py"


def get_cst_now():
    return datetime.now(SH_TZ)


def run_script(path, *args):
    cmd = ["python3", path] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


# ── 日历 ────────────────────────────────────────────────

def fetch_events_today():
    """今日所有日程，返回 [(time_str, summary), ...]"""
    out = run_script(CAL_LIST, "--today")
    return _parse_events_output(out)


def fetch_events_tomorrow():
    """明日所有日程，返回 [(time_str, summary), ...]"""
    out = run_script(CAL_LIST, "--tomorrow")
    return _parse_events_output(out)


def _parse_events_output(raw: str) -> list:
    """从 list_events.py 输出中提取 HH:MM 标题行"""
    lines = raw.split("\n")
    events = []
    for line in lines[1:]:  # 跳过标题行
        line = line.strip()
        if not line or "暂无" in line:
            continue
        # 格式: "  05/22 16:20 ~ 05/22 19:23  标题"
        m = re.match(r"^\d{2}/\d{2}\s+(\d{2}:\d{2})\s+~\s+\d{2}/\d{2}\s+\d{2}:\d{2}\s+(.+)$", line)
        if m:
            events.append((m.group(1), m.group(2)))
            continue
    return events


# ── 任务 ────────────────────────────────────────────────

def fetch_todos():
    """获取所有未完成任务，返回 [(summary, due_str, overdue_days), ...]"""
    out = run_script(TASK_LIST, "--status", "todo")
    tasks = []
    lines = out.split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("📋") or "暂无" in line:
            continue
        # 匹配 "  ○ 标题  截止 MM/DD" 或 "  ○ 标题  截止 无期限"
        m = re.match(r"^○\s+(.+?)\s+截止\s+(\d{2}/\d{2}|无期限)$", line)
        if m:
            title = m.group(1).strip()
            due_str = m.group(2)
            overdue_days = None
            if due_str != "无期限":
                due_month, due_day = int(due_str[:2]), int(due_str[3:])
                today = get_cst_now().date()
                due_this_year = datetime(today.year, due_month, due_day).date()
                due_next_year = datetime(today.year + 1, due_month, due_day).date()
                candidates = [due_this_year, due_next_year]
                overdue_candidates = [d for d in candidates if d < today]
                if overdue_candidates:
                    overdue_days = (today - min(overdue_candidates, key=lambda d: today - d)).days
            tasks.append((title, due_str, overdue_days))
    return tasks


# ── 格式化 ──────────────────────────────────────────────

def format_header():
    now = get_cst_now()
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    day_name = day_names[now.weekday()]
    date_str = now.strftime("%Y-%m-%d")
    print(f"📌 {date_str} {day_name}")
    print()


def format_today_events(events):
    print("☀️ 今日日程")
    if not events:
        print("  （暂无安排 🎉）")
        return
    for t, title in events:
        print(f"  {t} {title}")


def classify_tasks(tasks):
    """将任务分为逾期+今天截止 vs 未来截止"""
    today = get_cst_now().date()
    urgent, future = [], []
    for title, due_str, overdue_days in tasks:
        if overdue_days is not None:
            urgent.append((title, due_str, overdue_days))
        elif due_str == "无期限":
            future.append((title, due_str, None))
        else:
            # 今天截止（已排除逾期，上面算过了）
            due_month, due_day = int(due_str[:2]), int(due_str[3:])
            due_this_year = datetime(today.year, due_month, due_day).date()
            due_next_year = datetime(today.year + 1, due_month, due_day).date()
            candidates = [d for d in [due_this_year, due_next_year] if d >= today]
            due_date = min(candidates) if candidates else due_this_year
            if due_date == today:
                urgent.append((title, due_str, None))
            else:
                future.append((title, due_str, None))
    urgent.sort(key=lambda x: x[1])
    future.sort(key=lambda x: x[1] or "")
    return urgent, future


def format_today_todos(tasks):
    print()
    print("📋 今日待办")
    urgent, future = classify_tasks(tasks)

    if not urgent:
        print("  （全部完成 🎉）")
    else:
        for title, due_str, overdue_days in urgent:
            if overdue_days is not None:
                print(f"  ⚠️ {title}  逾期{overdue_days}天")
            else:
                print(f"  ○ {title}  截止 {due_str}")

    total_future = len(future)
    if total_future:
        print(f"  （+{total_future}项后续待办）")


def format_future_todos(tasks):
    print()
    print("📋 后续待办")
    _, future = classify_tasks(tasks)
    if not future:
        print("  （暂无）")
        return
    for title, due_str, _ in future:
        print(f"  ○ {title}  截止 {due_str}")


def format_tomorrow_events(events):
    print()
    total = len(events)
    label = f"📅 明日日程（{total}项）"
    if total == 0:
        print(label)
        print("  （暂无预告 🎉）")
        return
    shown = events[:3]
    print(label)
    for t, title in shown:
        print(f"  {t} {title}")


def main():
    format_header()
    today_ev = fetch_events_today()
    tomorrow_ev = fetch_events_tomorrow()
    todos = fetch_todos()

    format_today_events(today_ev)
    format_today_todos(todos)
    format_future_todos(todos)
    format_tomorrow_events(tomorrow_ev)


if __name__ == "__main__":
    main()
