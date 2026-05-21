#!/usr/bin/env python3
"""查看飞书日程，支持 --today / --tomorrow / --this-week / --next-week / --range"""
import subprocess, json, sys
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CALENDAR_ID = "<CALENDAR_ID>"

def parse_ts(ts_str):
    """解析秒级时间戳字符串为 datetime"""
    if not ts_str:
        return None
    try:
        return datetime.fromtimestamp(int(ts_str), tz=SH_TZ)
    except:
        return None

def calc_time_range():
    """根据命令行参数计算 start/end 时间戳（秒级）"""
    import argparse
    parser = argparse.ArgumentParser(description="查看飞书日程")
    parser.add_argument("--today", action="store_true", help="今天")
    parser.add_argument("--tomorrow", action="store_true", help="明天")
    parser.add_argument("--this-week", action="store_true", help="本周（周一~周日）")
    parser.add_argument("--next-week", action="store_true", help="下周")
    parser.add_argument("--range", nargs=2, metavar=("START", "END"), help="指定日期范围 YYYY-MM-DD YYYY-MM-DD")
    args = parser.parse_args(sys.argv[1:])

    now = datetime.now(tz=SH_TZ)
    today = now.date()

    if args.today:
        start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=SH_TZ)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=SH_TZ)
        label = f"今日日程（{today.strftime('%m/%d')}）"
    elif args.tomorrow:
        td = today + timedelta(days=1)
        start = datetime(td.year, td.month, td.day, 0, 0, 0, tzinfo=SH_TZ)
        end = datetime(td.year, td.month, td.day, 23, 59, 59, tzinfo=SH_TZ)
        label = f"明日日程（{td.strftime('%m/%d')}）"
    elif args.this_week:
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        start = datetime(monday.year, monday.month, monday.day, 0, 0, 0, tzinfo=SH_TZ)
        end = datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59, tzinfo=SH_TZ)
        label = f"本周日程（{monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}）"
    elif args.next_week:
        monday = today + timedelta(days=(7 - today.weekday()))
        sunday = monday + timedelta(days=6)
        start = datetime(monday.year, monday.month, monday.day, 0, 0, 0, tzinfo=SH_TZ)
        end = datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59, tzinfo=SH_TZ)
        label = f"下周日程（{monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}）"
    elif args.range:
        try:
            start_dt = datetime.strptime(args.range[0], "%Y-%m-%d")
            end_dt = datetime.strptime(args.range[1], "%Y-%m-%d")
            start = start_dt.replace(tzinfo=SH_TZ)
            end = end_dt.replace(hour=23, minute=59, second=59, tzinfo=SH_TZ)
            label = f"日程（{args.range[0]} ~ {args.range[1]}）"
        except ValueError:
            print("❌ 日期格式错误，请使用 YYYY-MM-DD")
            sys.exit(1)
    else:
        # 默认今天
        start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=SH_TZ)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=SH_TZ)
        label = f"今日日程（{today.strftime('%m/%d')}）"

    return int(start.timestamp()), int(end.timestamp()), label

def fetch_events(start_ts, end_ts):
    """调用 lark-cli 按时间范围查询日程"""
    all_items = []
    page_token = None

    while True:
        params = {
            "calendar_id": CALENDAR_ID,
            "start_time": str(start_ts),
            "end_time": str(end_ts),
            "page_size": 500
        }
        if page_token:
            params["page_token"] = page_token

        result = subprocess.run(
            ["lark-cli", "calendar", "events", "instance_view",
             "--params", json.dumps(params),
             "--format", "json"],
            capture_output=True, text=True
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            # lark-cli 输出含 [deprecated] 前缀时会导致 JSON 解析失败，尝试去掉前缀行
            lines = result.stdout.strip().split("\n")
            for i, line in enumerate(lines):
                try:
                    data = json.loads(line)
                    break
                except:
                    continue
            else:
                print(f"❌ 解析失败: {result.stdout[:200]}", file=sys.stderr)
                return []

        items = data.get("data", {}).get("items", [])
        all_items.extend(items)

        has_more = data.get("data", {}).get("has_more", False)
        if not has_more:
            break
        page_token = data.get("data", {}).get("page_token")
        if not page_token:
            break

    return all_items

def classify_event(event, now):
    """对日程进行状态分类"""
    start_ts_str = event.get("start_time", {}).get("timestamp", "")
    end_ts_str = event.get("end_time", {}).get("timestamp", "")
    status = event.get("status", "confirmed")

    if not start_ts_str:
        return "unknown", None, None

    start_dt = parse_ts(start_ts_str)
    end_dt = parse_ts(end_ts_str) if end_ts_str else None

    if status == "cancelled":
        return "cancelled", start_dt, end_dt
    if end_dt and end_dt < now:
        return "finished", start_dt, end_dt
    if start_dt and start_dt.date() == now.date():
        return "today", start_dt, end_dt
    if start_dt and start_dt.date() == now.date() + timedelta(days=1):
        return "tomorrow", start_dt, end_dt
    return "upcoming", start_dt, end_dt

def format_time_range(start_dt, end_dt):
    """格式化时间范围"""
    if not start_dt:
        return "时间待定"
    date_str = start_dt.strftime("%m/%d")
    if end_dt:
        start_time = start_dt.strftime("%H:%M")
        end_time = end_dt.strftime("%H:%M")
        return f"{date_str} {start_time}-{end_time}"
    return f"{date_str} {start_dt.strftime('%H:%M')}"

def render_events(events, label):
    """格式化输出日程列表"""
    now = datetime.now(tz=SH_TZ)

    # 分类
    cancelled, finished, today_list, tomorrow_list, upcoming = [], [], [], [], []

    for e in events:
        category, start_dt, end_dt = classify_event(e, now)
        summary = e.get("summary") or "（无标题）"
        event_id = e.get("event_id", "")

        entry = {
            "summary": summary,
            "event_id": event_id,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "time_str": format_time_range(start_dt, end_dt),
            "location": e.get("location", {}).get("name", ""),
        }

        if category == "cancelled":
            cancelled.append(entry)
        elif category == "finished":
            finished.append(entry)
        elif category == "today":
            today_list.append(entry)
        elif category == "tomorrow":
            tomorrow_list.append(entry)
        else:
            upcoming.append(entry)

    # 按开始时间排序
    def sort_key(e):
        return e["start_dt"] or datetime.max
    cancelled.sort(key=sort_key)
    finished.sort(key=sort_key)
    today_list.sort(key=sort_key)
    tomorrow_list.sort(key=sort_key)
    upcoming.sort(key=sort_key)

    # 输出
    print(f"📅 {label}")
    print("━" * 40)

    if not events:
        print("  （暂无日程）")
        return

    if cancelled:
        print("⚠️  已取消")
        for e in cancelled:
            loc = f" | 📍 {e['location']}" if e['location'] else ""
            print(f"  {e['time_str']} | {e['summary']}{loc}")
        print()

    if today_list:
        print("🔴 今天")
        for e in today_list:
            loc = f" | 📍 {e['location']}" if e['location'] else ""
            print(f"  {e['time_str']} | {e['summary']}{loc}")
        print()

    if tomorrow_list:
        print("🟡 明天")
        for e in tomorrow_list:
            loc = f" | 📍 {e['location']}" if e['location'] else ""
            print(f"  {e['time_str']} | {e['summary']}{loc}")
        print()

    if upcoming:
        print("📅 即将到来")
        for e in upcoming:
            loc = f" | 📍 {e['location']}" if e['location'] else ""
            print(f"  {e['time_str']} | {e['summary']}{loc}")
        print()

    if finished:
        print("⏸️  已结束")
        for e in finished:
            loc = f" | 📍 {e['location']}" if e['location'] else ""
            print(f"  {e['time_str']} | {e['summary']}{loc}")

    total = len(events)
    print(f"\n共 {total} 条")

if __name__ == "__main__":
    start_ts, end_ts, label = calc_time_range()
    events = fetch_events(start_ts, end_ts)
    render_events(events, label)
