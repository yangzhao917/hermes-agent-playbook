#!/usr/bin/env python3
"""删除飞书日程"""
import subprocess, json, sys
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CALENDAR_ID = "<CALENDAR_ID>"

def get_event_info(event_id):
    """获取日程信息用于确认"""
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
        lines = result.stdout.strip().split("\n")
        for line in lines:
            try:
                data = json.loads(line)
                break
            except:
                continue
        else:
            return None
    if data.get("code") != 0:
        return None
    return data.get("data", {}).get("event")

def parse_ts(ts_str):
    if not ts_str:
        return None
    try:
        return datetime.fromtimestamp(int(ts_str), tz=SH_TZ)
    except:
        return None

def delete_event(event_id, summary=None, time_str=None, dry_run=False):
    """删除日程"""
    if dry_run:
        print(f"[dry-run] 将会删除：")
        print(f"  ID: {event_id}")
        if summary:
            print(f"  标题: {summary}")
        if time_str:
            print(f"  时间: {time_str}")
        return {"ok": True, "dry_run": True}

    params = {
        "calendar_id": CALENDAR_ID,
        "event_id": event_id
    }
    result = subprocess.run(
        ["lark-cli", "calendar", "events", "delete",
         "--params", json.dumps(params),
         "--format", "json"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        lines = result.stdout.strip().split("\n")
        for line in lines:
            try:
                data = json.loads(line)
                break
            except:
                continue
        else:
            return {"ok": False, "error": f"无法解析输出: {result.stdout[:200]}"}

    if data.get("code") == 0 or data.get("ok"):
        return {"ok": True, "event_id": event_id}
    else:
        return {"ok": False, "error": data.get("msg", "删除失败")}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="删除飞书日程")
    parser.add_argument("--event-id", required=True, help="日程 ID")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟，不实际删除")
    parser.add_argument("--yes", action="store_true", help="跳过确认直接删除")
    args = parser.parse_args(sys.argv[1:])

    # 先获取日程信息用于友好提示
    event = get_event_info(args.event_id)

    if not event and not args.yes:
        print("⚠️  未能获取日程信息，是否仍要删除？")
        print(f"  ID: {args.event_id}")
        confirm = input("输入 'yes' 确认删除: ")
        if confirm.strip().lower() != "yes":
            print("已取消")
            sys.exit(0)
    elif event:
        summary = event.get("summary", "（无标题）")
        start_ts = event.get("start_time", {}).get("timestamp", "")
        start_dt = parse_ts(start_ts)
        time_str = start_dt.strftime("%m/%d %H:%M") if start_dt else "时间待定"

        if args.dry_run:
            result = delete_event(args.event_id, summary, time_str, dry_run=True)
        elif not args.yes:
            print(f"⚠️  确认删除以下日程？")
            print(f"  标题: {summary}")
            print(f"  时间: {time_str}")
            print(f"  ID: {args.event_id}")
            confirm = input("输入 'yes' 确认删除: ")
            if confirm.strip().lower() != "yes":
                print("已取消")
                sys.exit(0)
            result = delete_event(args.event_id)
        else:
            result = delete_event(args.event_id)

        if result.get("ok"):
            if not result.get("dry_run"):
                print(f"✅ 日程已删除")
                print(f"   标题: {summary}")
                print(f"   时间: {time_str}")
        else:
            print(f"❌ 删除失败: {result.get('error')}")
            sys.exit(1)
