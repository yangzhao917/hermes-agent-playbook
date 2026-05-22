#!/usr/bin/env python3
"""
飞书日历查询脚本，支持日期参数。
用法:
  python3 feishu_calendar.py today
  python3 feishu_calendar.py tomorrow
  python3 feishu_calendar.py 2026-05-25
依赖: ~/.hermes/feishu_user_token.json (OAuth user token)
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

TOKEN_FILE = os.path.expanduser("~/.hermes/feishu_user_token.json")
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")


def get_access_token():
    """读取当前 access_token（不刷新，过期由调用方处理）。"""
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    return data.get("access_token", "")


def refresh_token():
    """刷新 access_token 和 refresh_token。"""
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    old_refresh = data.get("refresh_token")
    if not old_refresh:
        return None

    url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": old_refresh,
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }).encode()

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        if result.get("code") == 0:
            d = result["data"]
            data["access_token"] = d["access_token"]
            data["refresh_token"] = d["refresh_token"]
            with open(TOKEN_FILE, "w") as f:
                json.dump(data, f, indent=2)
            return d["access_token"]
    except Exception:
        pass
    return None


def get_primary_calendar_id(token: str) -> str | None:
    """获取用户主日历 ID。"""
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/calendar/v4/calendars?page_size=50",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        for cal in data.get("data", {}).get("calendar_list", []):
            if cal.get("type") == "primary":
                return cal.get("calendar_id")
    except Exception:
        pass
    return None


def get_events(token: str, cal_id: str, date_str: str) -> list:
    """获取指定日期的日历事件。date_str 格式 YYYY-MM-DD。"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start_ts = int(datetime(dt.year, dt.month, dt.day, 0, 0, 0,
                            tzinfo=timezone(timedelta(hours=8))).timestamp())
    end_ts = int(datetime(dt.year, dt.month, dt.day, 23, 59, 59,
                          tzinfo=timezone(timedelta(hours=8))).timestamp())

    url = (f"https://open.feishu.cn/open-apis/calendar/v4/calendars/"
           f"{urllib.request.quote(cal_id)}/events"
           f"?page_size=50&start_time={start_ts}&end_time={end_ts}")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("data", {}).get("items", [])
    except urllib.error.HTTPError as e:
        if e.code == 401:
            new_token = refresh_token()
            if new_token:
                return get_events(new_token, cal_id, date_str)
        return []
    except Exception:
        return []


def format_time(start_obj):
    """从 start_time 对象提取时间字符串。"""
    if not start_obj:
        return ""
    # all-day event: {"date": "2026-05-22"}
    if "date" in start_obj:
        return start_obj["date"]
    # timed event: {"timestamp": "...", "timezone": "Asia/Shanghai"}
    ts = start_obj.get("timestamp")
    if ts:
        dt = datetime.fromtimestamp(int(ts), tz=timezone(timedelta(hours=8)))
        return dt.strftime("%H:%M")
    return ""


def main():
    if len(sys.argv) < 2:
        date_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    elif sys.argv[1] == "today":
        date_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    elif sys.argv[1] == "tomorrow":
        dt = datetime.now(timezone(timedelta(hours=8))) + timedelta(days=1)
        date_str = dt.strftime("%Y-%m-%d")
    else:
        date_str = sys.argv[1]

    token = get_access_token()
    if not token:
        print("❌ 未找到 user token，需重新授权")
        sys.exit(1)

    cal_id = get_primary_calendar_id(token)
    if not cal_id:
        print("❌ 无法获取日历 ID，token 可能已过期")
        sys.exit(1)

    events = get_events(token, cal_id, date_str)
    valid_events = [ev for ev in events if ev.get("status") != "cancelled"]

    if not valid_events:
        print(f"📅 {date_str} 无日程")
        return

    for ev in valid_events:
        start = format_time(ev.get("start_time"))
        end = format_time(ev.get("end_time"))
        summary = ev.get("summary") or "无标题"
        loc = ev.get("location", {}).get("location", "")
        loc_str = f" @{loc}" if loc else ""
        print(f"  {start}-{end} {summary}{loc_str}")


if __name__ == "__main__":
    main()
