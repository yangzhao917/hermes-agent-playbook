#!/usr/bin/env python3
"""
feishu-calendar: create_event.py
创建飞书日历日程
"""

import argparse
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="创建飞书日程")
    parser.add_argument("--summary", required=True, help="日程标题")
    parser.add_argument("--start", required=True, help="开始时间 ISO格式: 2026-05-25T14:00 或 2026-05-25T14:00+08:00")
    parser.add_argument("--end", required=True, help="结束时间 ISO格式")
    parser.add_argument("--calendar-id", default="feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn",
                        help="日历 ID（默认用户个人日历）")
    parser.add_argument("--attendee-ids", default="", help="参与人 open_id，逗号分隔")
    args = parser.parse_args()

    cmd = [
        "lark-cli", "calendar", "+create",
        "--summary", args.summary,
        "--start", args.start,
        "--end", args.end,
        "--calendar-id", args.calendar_id,
    ]
    if args.attendee_ids:
        cmd += ["--attendee-ids", args.attendee_ids]

    result = subprocess.run(cmd, capture_output=True, text=True)
    # 解析响应
    data = _parse_json(result.stdout + result.stderr)

    if data and data.get("code") == 0:
        event = data.get("data", {}).get("event", {})
        print(f"✅ 日程创建成功: {event.get('summary', args.summary)}")
        print(f"   event_id: {event.get('event_id', '')}")
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
