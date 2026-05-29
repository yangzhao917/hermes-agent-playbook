#!/usr/bin/env python3
"""
feishu-task: delete_task.py
删除任务
- 参数是 --params '{"task_guid":"..."}'，不是 --task-id
- 必须加 --yes
"""

import argparse
import json
import subprocess
import sys
import os


def main():
    parser = argparse.ArgumentParser(description="删除任务")
    parser.add_argument("--task-guid", required=True, help="任务 guid")
    parser.add_argument("--yes", action="store_true", help="跳过确认")
    args = parser.parse_args()

    if not args.yes:
        confirm = input(f"确认删除任务 {args.task_guid}？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消")
            return

    # lark-cli 要求 @file 必须是相对路径，写到当前目录
    params_file = "./params_delete.json"
    with open(params_file, "w") as f:
        json.dump({"task_guid": args.task_guid}, f)

    cmd = ["lark-cli", "task", "tasks", "delete", "--params", f"@{params_file}", "--yes"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(params_file)

    data = _parse_json(result.stdout + result.stderr)
    if data and data.get("code") == 0:
        print("✅ 任务已删除")
    else:
        print(f"❌ 删除失败: {data}", file=sys.stderr)
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
