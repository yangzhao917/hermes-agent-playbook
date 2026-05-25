#!/usr/bin/env python3
"""
feishu-task: create_task.py
创建飞书任务
- --due 支持相对格式（+2d, +1w）或绝对日期（2026-05-25）
- --assignee 默认当前用户
"""

import argparse
import json
import subprocess
import sys


USER_OPEN_ID = "ou_5b875f5ec5752b06832bb240ad482ec0"


def main():
    parser = argparse.ArgumentParser(description="创建飞书任务")
    parser.add_argument("--summary", required=True, help="任务标题")
    parser.add_argument("--due", required=True,
                       help="截止时间：绝对日期(2026-05-25) 或相对时间(+2d, +1w)")
    parser.add_argument("--assignee", default=USER_OPEN_ID,
                       help="负责人 open_id（默认当前用户）")
    args = parser.parse_args()

    cmd = [
        "lark-cli", "task", "+create",
        "--summary", args.summary,
        "--due", args.due,
        "--assignee", args.assignee,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    data = _parse_json(result.stdout + result.stderr)

    if data and data.get("ok") is True:
        task = data.get("data", {}).get("task", {})
        print(f"✅ 任务创建成功")
        print(f"   标题: {task.get('summary', args.summary)}")
        print(f"   截止: {args.due}")
        print(f"   guid: {task.get('guid', '')}")
    else:
        print(f"❌ 创建失败: {data}", file=sys.stderr)
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
