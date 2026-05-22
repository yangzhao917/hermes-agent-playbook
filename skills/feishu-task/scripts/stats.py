#!/usr/bin/env python3
"""
飞书任务统计概览：已过期/今日到期/未来任务。
"""
import json
import subprocess
from datetime import datetime, timezone, timedelta


def get_tasks(completed: bool):
    params = {"page_size": 50, "completed": completed}
    result = subprocess.run(
        ["lark-cli", "task", "tasks", "list",
         "--params", json.dumps(params), "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        if data.get("code") != 0:
            return []
        return data.get("data", {}).get("items", [])
    except json.JSONDecodeError:
        return []


def main():
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    today_dt = datetime.now(timezone(timedelta(hours=8))).date()

    incomplete = get_tasks(False)
    overdue, today_t, upcoming = [], [], []

    for t in incomplete:
        due_obj = t.get("due", {})
        ts = due_obj.get("timestamp") if due_obj else None
        if not ts:
            continue
        due_dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone(timedelta(hours=8))).date()
        summary = t.get("summary", "")
        if due_dt < today_dt:
            overdue.append((due_dt.strftime("%m/%d"), summary))
        elif due_dt == today_dt:
            today_t.append(summary)
        else:
            upcoming.append((due_dt.strftime("%m/%d"), summary))

    overdue.sort()
    upcoming.sort()
    today_t.sort()

    print(f"📊 任务统计")
    print(f"  🔴 已过期({len(overdue)}):")
    for d, s in overdue:
        print(f"    ⚠️ {d} {s}")
    print(f"  🔴 今日到期({len(today_t)}):")
    for s in today_t:
        print(f"    ☐ {s}")
    print(f"  🟡 近期待办({len(upcoming)}):")
    for d, s in upcoming:
        print(f"    ☐ {d} {s}")


if __name__ == "__main__":
    main()
