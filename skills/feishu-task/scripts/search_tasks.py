#!/usr/bin/env python3
"""
feishu-task: search_tasks.py
搜索任务
- --completed 是 flag（不是 --complete）
- 不传 --completed 则搜索全部
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta


SH_TZ = timezone(timedelta(hours=8))


def fmt_due(ts):
    if not ts or ts == "0":
        return "无期限"
    return datetime.fromtimestamp(int(ts) / 1000, tz=SH_TZ).strftime("%m/%d")


def main():
    parser = argparse.ArgumentParser(description="搜索任务")
    parser.add_argument("--query", required=True, help="关键词")
    parser.add_argument("--completed", type=str, choices=["true", "false"],
                        help="是否已完成（不传则搜索全部）")
    args = parser.parse_args()

    cmd = ["lark-cli", "task", "+search", "--query", args.query, "--format", "json"]
    if args.completed == "true":
        cmd.append("--completed")
    elif args.completed == "false":
        # --completed false 不存在，用不过滤
        pass

    cmd.append("--page-all")

    result = subprocess.run(cmd, capture_output=True, text=True)
    data = _parse_json(result.stdout + result.stderr)

    if not data or data.get("code") != 0:
        print(f"❌ 搜索失败: {data}", file=sys.stderr)
        sys.exit(1)

    tasks = data.get("data", {}).get("items", [])
    if not tasks:
        print(f"🔍 未找到包含「{args.query}」的任务")
        return

    print(f"🔍 找到 {len(tasks)} 个任务:")
    for t in tasks:
        due = fmt_due(t.get("due", {}).get("timestamp", "0") if isinstance(t.get("due"), dict) else "0")
        status = "✓" if t.get("status") == "done" else "○"
        summary = t.get("summary", "(无标题)")
        print(f"  {status} {summary}  截止 {due}  guid={t.get('guid','')}")


def _parse_json(stdout):
    """解析 lark-cli 的 --format json 输出
    - instance_view: 多行格式化 JSON → 整段解析
    - tasks list: 紧凑单行 JSON → 整段解析
    - 含 [deprecated] 前缀时 → 提取大括号内部分
    """
    text = stdout.strip()
    if not text:
        return None
    # 策略一：直接解析整段（处理多行格式 JSON）
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 策略二：跳过前缀行，找第一个 { 开始解析
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("[") or line == "}":
            continue
        try:
            # 跳过 [deprecated] 等前缀
            brace_start = line.find("{")
            if brace_start >= 0:
                return json.loads(line[brace_start:])
        except json.JSONDecodeError:
            continue
    return None



if __name__ == "__main__":
    main()
