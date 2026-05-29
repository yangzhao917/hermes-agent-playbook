#!/usr/bin/env python3
"""
feishu-task: complete_task.py
完成任务（用 +complete，不是 patch）
- 成功返回 {"ok": true}，不是 {"code: 0}
"""

import argparse
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="完成任务")
    parser.add_argument("--task-id", required=True, help="任务 guid")
    args = parser.parse_args()

    cmd = ["lark-cli", "task", "+complete", "--task-id", args.task_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    raw = result.stdout + result.stderr

    # 判断成功：{"ok": true}
    data = _parse_json(raw)
    if data and data.get("ok") is True:
        print(f"✅ 任务已完成: {args.task_id}")
    else:
        print(f"❌ 完成任务失败: {data}", file=sys.stderr)
        sys.exit(1)


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
