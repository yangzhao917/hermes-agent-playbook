#!/usr/bin/env python3
"""
列出飞书任务，支持按完成状态过滤。
用法:
  python3 list_tasks.py --completed=false   # 未完成
  python3 list_tasks.py --completed=true     # 已完成
  python3 list_tasks.py                      # 全部
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta


def get_tasks(completed: bool | None):
    """获取任务列表。completed=None表示全部，True=已完成，False=未完成"""
    params = {"page_size": 50}
    if completed is not None:
        params["completed"] = completed

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


def format_due(due_obj):
    """格式化截止日期"""
    if not due_obj:
        return ""
    ts = due_obj.get("timestamp")
    if not ts:
        return ""
    dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%m/%d")


def main():
    parser = argparse.ArgumentParser(description="列出飞书任务")
    parser.add_argument("--completed", type=str, choices=["true", "false"])
    args = parser.parse_args()

    if args.completed == "true":
        completed = True
    elif args.completed == "false":
        completed = False
    else:
        completed = None

    tasks = get_tasks(completed)
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")

    if not tasks:
        print("无任务")
        return

    for t in tasks:
        due_obj = t.get("due", {})
        due_str = format_due(due_obj)
        summary = t.get("summary", "")
        status = t.get("status", "")
        is_done = status == "done"

        if completed is None:
            # 全部模式，按状态分组显示
            flag = "✅" if is_done else "🔴"
            due_display = f"[{due_str}]" if due_str else "[  ]"
            print(f"{flag} {due_display} {summary}")
        elif completed:
            print(f"✅ [{due_str}] {summary}")
        else:
            print(f"🔴 [{due_str}] {summary}")


if __name__ == "__main__":
    main()
