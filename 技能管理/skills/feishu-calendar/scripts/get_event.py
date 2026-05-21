#!/usr/bin/env python3
"""查看单条日程详情"""
import subprocess, json, sys
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CALENDAR_ID = "<CALENDAR_ID>"

def parse_ts(ts_str):
    if not ts_str:
        return None
    try:
        return datetime.fromtimestamp(int(ts_str), tz=SH_TZ)
    except:
        return None

def fetch_event(event_id):
    """获取单条日程详情"""
    params = {
        "calendar_id": CALENDAR_ID,
        "event_id": event_id
    }
    result = subprocess.run(
        ["lark-cli", "calendar", "events", "get",
         "--params", json.dumps(params),
         "--format", "json"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        # 尝试去掉 [deprecated] 等前缀行
        lines = result.stdout.strip().split("\n")
        for line in lines:
            try:
                data = json.loads(line)
                break
            except:
                continue
        else:
            print(f"❌ 解析失败: {result.stdout[:200]}", file=sys.stderr)
            return None

    if data.get("code") != 0:
        print(f"❌ 获取失败: {data.get('msg', '未知错误')}")
        return None

    return data.get("data", {}).get("event")

def render_event(event):
    """格式化展示单条日程"""
    if not event:
        return

    summary = event.get("summary") or "（无标题）"
    description = event.get("description", "")

    start_ts = event.get("start_time", {}).get("timestamp", "")
    end_ts = event.get("end_time", {}).get("timestamp", "")
    start_dt = parse_ts(start_ts)
    end_dt = parse_ts(end_ts)

    status = event.get("status", "confirmed")
    status_map = {
        "tentative": "⏳ 待确认",
        "confirmed": "✅ 已确认",
        "cancelled": "❌ 已取消",
    }
    status_str = status_map.get(status, status)

    # 时间显示
    if start_dt:
        if end_dt:
            time_str = f"{start_dt.strftime('%Y/%m/%d %H:%M')} ~ {end_dt.strftime('%H:%M')}"
        else:
            time_str = start_dt.strftime("%Y/%m/%d %H:%M")
    else:
        time_str = "时间待定"

    location = event.get("location", {})
    location_name = location.get("name", "")
    location_addr = location.get("address", "")

    organizer = event.get("event_organizer", {})
    organizer_name = organizer.get("display_name", "")

    reminders = event.get("reminders", [])
    reminder_str = "无" if not reminders else ", ".join([f"开始前{r.get('minutes', 0)}分钟" for r in reminders])

    recurrence = event.get("recurrence", "")

    print(f"📋 {summary}")
    print("━" * 40)
    print(f"🕐 时间：{time_str}")
    print(f"📌 状态：{status_str}")
    if location_name:
        print(f"📍 地点：{location_name}")
        if location_addr:
            print(f"   地址：{location_addr}")
    if organizer_name:
        print(f"👤 组织者：{organizer_name}")
    print(f"🔔 提醒：{reminder_str}")
    if recurrence:
        print(f"🔄 重复：{recurrence}")
    if description:
        desc_preview = description[:100] + ("..." if len(description) > 100 else "")
        print(f"📝 描述：{desc_preview}")
    print(f"🆔 ID：{event.get('event_id', '')}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查看单条日程详情")
    parser.add_argument("--event-id", required=True, help="日程 ID")
    args = parser.parse_args(sys.argv[1:])

    event = fetch_event(args.event_id)
    render_event(event)
