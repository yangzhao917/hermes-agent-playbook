#!/usr/bin/env python3
"""
feishu-calendar: freebusy.py
查询用户在指定时间段内的忙闲状态
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta


SH_TZ = timezone(timedelta(hours=8))


def main():
    parser = argparse.ArgumentParser(description="查询忙闲")
    parser.add_argument("--user-id", required=True, help="飞书 open_id")
    parser.add_argument("--start", required=True, help="开始时间 ISO格式")
    parser.add_argument("--end", required=True, help="结束时间 ISO格式")
    args = parser.parse_args()

    result = subprocess.run(
        ["lark-cli", "calendar", "+freebusy",
         "--user-id", args.user_id,
         "--start", args.start,
         "--end", args.end,
         "--format", "json"],
        capture_output=True, text=True
    )

    data = _parse_json(result.stdout + result.stderr)
    if not data or data.get("code") != 0:
        print(f"❌ 查询失败: {data}", file=sys.stderr)
        sys.exit(1)

    time_slots = data.get("data", {}).get("time_slots", [])
    if not time_slots:
        print("📅 暂无日程安排")
        return

    print("📅 忙闲状态")
    for slot in time_slots:
        fb = slot.get("fb_event", [])
        if not fb:
            print(f"  {slot['start_time']} ~ {slot['end_time']}  空")
        else:
            for e in fb:
                print(f"  {e.get('start_time','')} ~ {e.get('end_time','')}  {e.get('summary','(无标题)')}")


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
