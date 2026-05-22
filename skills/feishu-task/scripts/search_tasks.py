#!/usr/bin/env python3
"""
搜索飞书任务。
用法: python3 search_tasks.py --query "关键词"
"""
import argparse
import json
import subprocess
from datetime import datetime, timezone, timedelta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    result = subprocess.run(
        ["lark-cli", "task", "+search", args.query, "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("搜索失败")
        return
    try:
        data = json.loads(result.stdout)
        tasks = data if isinstance(data, list) else data.get("data", {}).get("items", [])
    except json.JSONDecodeError:
        tasks = []

    if not tasks:
        print("未找到任务")
        return

    for t in tasks:
        due_obj = t.get("due", {})
        ts = due_obj.get("timestamp") if due_obj else None
        if ts:
            due_str = datetime.fromtimestamp(int(ts)/1000, tz=timezone(timedelta(hours=8))).strftime("%m/%d")
        else:
            due_str = "-"
        print(f"[{due_str}] {t.get('summary')}")


if __name__ == "__main__":
    main()
