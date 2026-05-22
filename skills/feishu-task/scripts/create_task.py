#!/usr/bin/env python3
"""
创建飞书任务。
用法: python3 create_task.py --summary "任务标题" --due "+2d"
     python3 create_task.py --summary "任务标题" --due "2026-05-25"
"""
import argparse
import json
import subprocess
from datetime import datetime, timezone, timedelta


def parse_due(due_str: str) -> str:
    """解析截止日期，返回 ISO8601 字符串。"""
    if due_str.startswith("+"):
        days = int(due_str[1:])
        dt = datetime.now(timezone(timedelta(hours=8))) + timedelta(days=days)
        return dt.isoformat()
    return due_str


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--due", default="")
    args = parser.parse_args()

    data = {"summary": args.summary}
    if args.due:
        data["due"] = {"timestamp": str(int(datetime.fromisoformat(parse_due(args.due)).timestamp() * 1000))}

    result = subprocess.run(
        ["lark-cli", "task", "+create",
         "--data", json.dumps(data), "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ 任务已创建: {args.summary}")
    else:
        print(f"❌ 创建失败: {result.stderr}")


if __name__ == "__main__":
    main()
