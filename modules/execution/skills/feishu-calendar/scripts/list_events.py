#!/usr/bin/env python3
"""
feishu-calendar: list_events.py
查看飞书日历日程（支持今日/明日/指定日期/日期范围）
- 自动处理 40 天 API 限制，分段查询后合并结果
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CAL_ID = "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn"
MAX_SPAN_SECONDS = 40 * 24 * 60 * 60  # 40 days


def parse_ts(ts_str):
    return int(ts_str)


def fmt_dt(ts):
    return datetime.fromtimestamp(ts, tz=SH_TZ).strftime("%m/%d %H:%M")


def calc_timestamp(date_str):
    """把 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM 转成秒级时间戳"""
    dt = datetime.fromisoformat(date_str.replace("Z", "+08:00"))
    dt = dt.astimezone(SH_TZ)
    return int(dt.timestamp())


def get_weekday_label():
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return day_names[datetime.now(SH_TZ).weekday()]


def get_today_range():
    today = datetime.now(SH_TZ).date()
    start = datetime(today.year, today.month, today.day, tzinfo=SH_TZ)
    end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=SH_TZ)
    return int(start.timestamp()), int(end.timestamp())


def get_tomorrow_range():
    tomorrow = datetime.now(SH_TZ).date() + timedelta(days=1)
    start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=SH_TZ)
    end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59, tzinfo=SH_TZ)
    return int(start.timestamp()), int(end.timestamp())


def get_date_range(date_str):
    """指定单日 00:00 ~ 23:59:59"""
    dt = datetime.fromisoformat(date_str).astimezone(SH_TZ).date()
    start = datetime(dt.year, dt.month, dt.day, tzinfo=SH_TZ)
    end = datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=SH_TZ)
    return int(start.timestamp()), int(end.timestamp())


def fetch_events(cal_id, start_ts, end_ts):
    """调用 lark-cli instance_view，分段处理 40 天限制"""
    all_events = []
    cur = start_ts

    while cur < end_ts:
        seg_end = min(cur + MAX_SPAN_SECONDS, end_ts)
        params = {
            "calendar_id": cal_id,
            "start_time": str(cur),
            "end_time": str(seg_end),
        }
        result = subprocess.run(
            ["lark-cli", "calendar", "events", "instance_view",
             "--params", json.dumps(params), "--format", "json"],
            capture_output=True, text=True
        )
        # 解析 JSON（跳过 [deprecated] 前缀）
        data = _parse_json(result.stdout)
        if data and data.get("code") == 0:
            items = data.get("data", {}).get("items", [])
            all_events.extend(items)
        cur = seg_end

    # 去重（event_id + start_timestamp 唯一键）
    seen = set()
    unique = []
    for e in all_events:
        key = (e.get("event_id", ""), e["start_time"].get("timestamp", ""))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


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


def main():
    parser = argparse.ArgumentParser(description="查看飞书日历日程")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--today", action="store_true", help="今日日程")
    group.add_argument("--tomorrow", action="store_true", help="明日日程")
    group.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--start", type=str, help="范围起始 YYYY-MM-DD")
    parser.add_argument("--end", type=str, help="范围结束 YYYY-MM-DD")
    args = parser.parse_args()

    # 计算时间范围
    if args.today:
        start_ts, end_ts = get_today_range()
        label = f"{datetime.now(SH_TZ).strftime('%m/%d')} {get_weekday_label()}"
    elif args.tomorrow:
        start_ts, end_ts = get_tomorrow_range()
        tomorrow_date = datetime.now(SH_TZ).date() + timedelta(days=1)
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        label = f"{tomorrow_date.strftime('%m/%d')} {day_names[tomorrow_date.weekday()]}"
    elif args.date:
        start_ts, end_ts = get_date_range(args.date)
        label = args.date[5:]  # MM-DD
    elif args.start and args.end:
        start_ts = calc_timestamp(args.start)
        end_ts = calc_timestamp(args.end) + 86399  # 包含结束日整天
        label = f"{args.start} ~ {args.end}"
    else:
        # 默认今日
        start_ts, end_ts = get_today_range()
        label = f"{datetime.now(SH_TZ).strftime('%m/%d')} {get_weekday_label()}"

    events = fetch_events(CAL_ID, start_ts, end_ts)
    # 按开始时间排序
    events.sort(key=lambda x: x["start_time"].get("timestamp", "0"))

    if not events:
        print(f"📅 {label} 暂无安排 🎉")
        return

    print(f"📅 {label} 日程")
    for e in events:
        start = fmt_dt(int(e["start_time"]["timestamp"]))
        end = fmt_dt(int(e["end_time"]["timestamp"]))
        summary = e.get("summary", "(无标题)")
        status = e.get("status", "")
        if status == "cancelled":
            continue
        print(f"  {start} ~ {end}  {summary}")


if __name__ == "__main__":
    main()
