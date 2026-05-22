#!/usr/bin/env python3
"""
完成任务（模糊匹配任务名）。
用法: python3 complete_task.py --query "关键词"
"""
import argparse
import json
import subprocess
from difflib import SequenceMatcher


def search_tasks(query: str):
    result = subprocess.run(
        ["lark-cli", "task", "+search", query, "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else data.get("data", {}).get("items", [])
    except json.JSONDecodeError:
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    tasks = search_tasks(args.query)
    if not tasks:
        print("未找到任务")
        return

    # 模糊匹配，取最高分
    best_score, best_task = 0, None
    for t in tasks:
        score = SequenceMatcher(None, args.query.lower(), t.get("summary", "").lower()).ratio() * 100
        if score > best_score:
            best_score = score
            best_task = t

    if best_score < 60:
        print("匹配度太低，请输入更精确的关键词")
        return

    task_id = best_task.get("task_id") or best_task.get("guid")
    result = subprocess.run(
        ["lark-cli", "task", "+complete", task_id, "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ 已完成: {best_task['summary']}")
    else:
        print(f"❌ 失败: {result.stderr}")


if __name__ == "__main__":
    main()
