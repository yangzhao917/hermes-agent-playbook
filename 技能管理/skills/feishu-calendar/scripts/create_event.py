#!/usr/bin/env python3
"""创建飞书日程"""
import subprocess, json, sys
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CALENDAR_ID = "<CALENDAR_ID>"

def parse_time(time_str):
    """解析时间字符串为 datetime"""
    formats = [
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.replace(tzinfo=SH_TZ)
        except ValueError:
            continue
    return None

def create_event(summary, start_str, end_str, description=None, location=None, dry_run=False):
    """创建日程"""
    start_dt = parse_time(start_str)
    end_dt = parse_time(end_str)

    if not start_dt:
        return {"ok": False, "error": f"无法解析开始时间: {start_str}"}
    if not end_dt:
        return {"ok": False, "error": f"无法解析结束时间: {end_str}"}
    if end_dt <= start_dt:
        return {"ok": False, "error": "结束时间必须晚于开始时间"}

    start_ts = str(int(start_dt.timestamp()))
    end_ts = str(int(end_dt.timestamp()))

    cmd = [
        "lark-cli", "calendar", "+create",
        "--summary", summary,
        "--start", f"{start_ts}",   # lark-cli 会解析秒级时间戳
        "--end", f"{end_ts}",
        "--calendar-id", CALENDAR_ID,
        "--format", "json"
    ]

    if description:
        cmd.extend(["--description", description])
    if location:
        cmd.extend(["--location", location])

    if dry_run:
        cmd.append("--dry-run")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {"ok": True, "dry_run": True, "output": result.stdout}

    result = subprocess.run(cmd, capture_output=True, text=True)
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

    # lark-cli +create 成功返回 ok: true
    if data.get("ok"):
        event_id = data.get("data", {}).get("event_id", "")
        url = data.get("data", {}).get("url", "")
        start_display = start_dt.strftime("%m/%d %H:%M")
        end_display = end_dt.strftime("%H:%M")
        return {
            "ok": True,
            "event_id": event_id,
            "url": url,
            "summary": summary,
            "time_range": f"{start_display}-{end_display}"
        }
    else:
        return {"ok": False, "error": data.get("msg", "创建失败")}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="创建飞书日程")
    parser.add_argument("--summary", required=True, help="日程标题")
    parser.add_argument("--start", required=True, help="开始时间，格式: YYYY-MM-DDTHH:MM 或 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="结束时间，格式: YYYY-MM-DDTHH:MM 或 YYYY-MM-DD")
    parser.add_argument("--description", help="日程描述")
    parser.add_argument("--location", help="地点")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟，不实际创建")
    args = parser.parse_args(sys.argv[1:])

    result = create_event(
        summary=args.summary,
        start_str=args.start,
        end_str=args.end,
        description=args.description,
        location=args.location,
        dry_run=args.dry_run
    )

    if result.get("dry_run"):
        print("[dry-run] 将会创建：")
        print(f"  标题: {args.summary}")
        print(f"  开始: {args.start}")
        print(f"  结束: {args.end}")
        if args.description:
            print(f"  描述: {args.description}")
        if args.location:
            print(f"  地点: {args.location}")
        sys.exit(0)
    elif result.get("ok"):
        print(f"✅ 日程已创建")
        print(f"   标题: {result['summary']}")
        print(f"   时间: {result['time_range']}")
        print(f"   ID: {result['event_id']}")
        if result.get("url"):
            print(f"   链接: {result['url']}")
    else:
        print(f"❌ 创建失败: {result.get('error')}")
        sys.exit(1)
