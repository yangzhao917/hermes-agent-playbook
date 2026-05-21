#!/usr/bin/env python3
"""统计概览：本周新增/完成/逾期/完成率 + 最久未完成 Top3"""
import subprocess, json, sys
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))

def get_week_range():
    """返回自然周（本周一 00:00 ~ 本周日 23:59:59）"""
    now = datetime.now(tz=SH_TZ)
    today = now.date()
    # Monday = 0, Sunday = 6
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    monday_dt = datetime(monday.year, monday.month, monday.day, 0, 0, 0, tzinfo=SH_TZ)
    sunday_dt = datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59, tzinfo=SH_TZ)
    return monday_dt, sunday_dt, monday, sunday

def fetch_tasks_paginated(completed: bool):
    all_items = []
    page_token = None
    while True:
        params = {"completed": completed, "page_size": 100}
        if page_token:
            params["page_token"] = page_token
        result = subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", json.dumps(params), "--format", "json"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        all_items.extend(data.get("data", {}).get("items", []))
        if not data.get("data", {}).get("has_more"):
            break
        page_token = data.get("data", {}).get("page_token")
        if not page_token:
            break
    return all_items

def parse_ts(ts_val):
    """解析各种时间戳格式为 datetime"""
    if not ts_val or ts_val == "0":
        return None
    try:
        return datetime.fromtimestamp(int(str(ts_val)[:10]), tz=SH_TZ)
    except:
        return None

def stats():
    monday_dt, sunday_dt, monday, sunday = get_week_range()
    today = datetime.now(tz=SH_TZ).date()

    all_todo = fetch_tasks_paginated(False)
    all_done = fetch_tasks_paginated(True)

    # 本周新增：created_at 在本周内（用 created_at 字段）
    week_new = []
    for t in all_todo + all_done:
        ct = t.get("created_at")
        if ct:
            if isinstance(ct, str):
                try:
                    ct_dt = datetime.fromisoformat(ct[:19]).replace(tzinfo=SH_TZ)
                except:
                    ct_dt = None
            else:
                ct_dt = parse_ts(str(ct))
            if ct_dt and monday_dt <= ct_dt <= sunday_dt:
                week_new.append(t)

    # 本周完成：completed_at 在本周内
    week_done = []
    for t in all_done:
        cat = t.get("completed_at")
        if cat and cat != "0":
            cat_dt = parse_ts(str(cat))
            if cat_dt and monday_dt <= cat_dt <= sunday_dt:
                week_done.append(t)

    # 逾期任务（截止日期 < 今天，且 status=todo）
    overdue = []
    for t in all_todo:
        due_ts = t.get("due", {}).get("timestamp", "0") if t.get("due") else "0"
        if due_ts and due_ts != "0":
            dt = parse_ts(due_ts)
            if dt and dt.date() < today:
                overdue.append((t, (today - dt.date()).days))

    overdue.sort(key=lambda x: x[1], reverse=True)

    # 计算完成率
    total_tasks = len(all_todo) + len(all_done)
    done_count = len(all_done)
    completion_rate = (done_count / total_tasks * 100) if total_tasks > 0 else 0

    print(f"📊 本周概览（{monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}）")
    print(f"   新增: {len(week_new)}  完成: {len(week_done)}  逾期: {len(overdue)}  完成率: {completion_rate:.1f}%")
    print(f"\n📋 当前任务状态：")
    print(f"   未完成: {len(all_todo)}  已完成: {done_count}")

    # 最久未完成 Top3（未完成任务中截止日期最早的）
    todo_with_due = [(t, parse_ts(t.get("due", {}).get("timestamp", ""))) for t in all_todo]
    todo_with_due = [(t, dt) for t, dt in todo_with_due if dt is not None]
    todo_with_due.sort(key=lambda x: x[1])

    if overdue:
        print(f"\n🔥 最久未完成 Top3（已逾期）")
        for i, (t, days) in enumerate(overdue[:3], 1):
            summary = t.get("summary", "(无标题)")
            print(f"   {i}. {summary}")
            due_dt = parse_ts(t.get("due", {}).get("timestamp", ""))
            due_str = due_dt.strftime("%m/%d") if due_dt else "未知"
            print(f"      截止: {due_str} | 逾期 {days} 天 | `{t.get('guid','')[:8]}`")
    elif todo_with_due:
        print(f"\n🔥 最久未完成 Top3（即将到期）")
        for i, (t, dt) in enumerate(todo_with_due[:3], 1):
            summary = t.get("summary", "(无标题)")
            delta = (dt.date() - today).days
            print(f"   {i}. {summary}")
            due_str = dt.strftime('%m/%d')
            if delta < 0:
                print(f"      截止: {due_str} | 逾期 {-delta} 天 | `{t.get('guid','')[:8]}`")
            elif delta == 0:
                print(f"      截止: {due_str} | 🔴 今天 | `{t.get('guid','')[:8]}`")
            else:
                print(f"      截止: {due_str} | `{t.get('guid','')[:8]}`")


if __name__ == "__main__":
    stats()
