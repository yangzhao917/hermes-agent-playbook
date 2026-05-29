#!/usr/bin/env python3
"""
feishu-calendar: delete_event.py
删除飞书日程
"""

import argparse
import json
import subprocess
import sys
import tempfile
import os
import shutil


CAL_ID = "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn"


def main():
    parser = argparse.ArgumentParser(description="删除飞书日程")
    parser.add_argument("--event-id", required=True, help="日程 event_id")
    parser.add_argument("--yes", action="store_true", help="跳过确认")
    args = parser.parse_args()

    if not args.yes:
        confirm = input(f"确认删除日程 {args.event_id}？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消")
            return

    tmpdir = tempfile.mkdtemp()
    params_file = os.path.join(tmpdir, "params.json")
    with open(params_file, "w") as f:
        json.dump({"calendar_id": CAL_ID, "event_id": args.event_id}, f)

    cmd = [
        "lark-cli", "calendar", "events", "delete",
        "--params", f"@{params_file}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)
    shutil.rmtree(tmpdir)

    data = _parse_json(result.stdout + result.stderr)
    if data and data.get("code") == 0:
        print("✅ 日程已删除")
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
