#!/usr/bin/env python3
"""
feishu-calendar: patch_event.py
修改飞书日程（标题/时间）
- 时间戳用 Python 计算（秒级）
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta


SH_TZ = timezone(timedelta(hours=8))
CAL_ID = "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn"


def calc_timestamp(dt_str):
    """ISO 日期字符串 → 秒级 Unix 时间戳"""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+08:00"))
    dt = dt.astimezone(SH_TZ)
    return int(dt.timestamp())


def main():
    parser = argparse.ArgumentParser(description="修改飞书日程")
    parser.add_argument("--event-id", required=True, help="日程 event_id")
    parser.add_argument("--summary", help="新标题")
    parser.add_argument("--start", help="新开始时间 ISO格式")
    parser.add_argument("--end", help="新结束时间 ISO格式")
    parser.add_argument("--description", help="新描述/备注")
    args = parser.parse_args()

    # 构建 patch 数据（只传提供的字段）
    data = {}
    if args.summary:
        data["summary"] = args.summary
    if args.start:
        data["start_time"] = {"timestamp": str(calc_timestamp(args.start)), "timezone": "Asia/Shanghai"}
    if args.end:
        data["end_time"] = {"timestamp": str(calc_timestamp(args.end)), "timezone": "Asia/Shanghai"}
    if args.description:
        data["description"] = args.description

    if not data:
        print("❌ 至少需要提供 --summary、--start、--end 或 --description 之一", file=sys.stderr)
        sys.exit(1)

    # lark-cli 要求 @file 必须是相对路径，写到当前目录
    import os
    data_file = "./patch_data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    params = {"calendar_id": CAL_ID, "event_id": args.event_id}
    params_file = "./patch_params.json"
    with open(params_file, "w") as f:
        json.dump(params, f)

    cmd = [
        "lark-cli", "calendar", "events", "patch",
        "--params", f"@{params_file}",
        "--data", f"@{data_file}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(data_file)
    os.remove(params_file)

    data_resp = _parse_json(result.stdout + result.stderr)
    if data_resp and data_resp.get("code") == 0:
        print(f"✅ 日程修改成功: {args.summary or '(内容更新)'}")
    else:
        print(f"❌ 修改失败: {data_resp}", file=sys.stderr)
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
