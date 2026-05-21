#!/usr/bin/env python3
"""列出飞书任务，支持分页，按截止日期排序"""
import json, sys, re
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))

def parse_due(ts_str):
    if not ts_str or ts_str == '0':
        return None
    try:
        return datetime.fromtimestamp(int(ts_str) / 1000, tz=SH_TZ)
    except:
        return None

def fetch_tasks(completed: bool, max_pages: int = 10):
    """分页拉取任务，返回列表"""
    all_items = []
    page_token = None

    for _ in range(max_pages):
        params = {"completed": completed, "page_size": 100}
        if page_token:
            params["page_token"] = page_token

        import subprocess, json
        result = subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", json.dumps(params),
             "--format", "json"],
            capture_output=True, text=True
        )
        try:
            data = json.loads(result.stdout)
        except:
            print(f"# ERROR parsing: {result.stdout[:200]}", file=sys.stderr)
            break

        if data.get("code") != 0:
            print(f"# API error: {data}", file=sys.stderr)
            break

        items = data.get("data", {}).get("items", [])
        all_items.extend(items)

        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token")
        if not has_more or not page_token:
            break

    return all_items

def render_tasks(tasks, show_completed: bool = False):
    now = datetime.now(tz=SH_TZ)
    overdue = []
    upcoming = []
    no_due = []

    for t in tasks:
        due_ts = t.get("due", {}).get("timestamp", "0") if t.get("due") else "0"
        dt = parse_due(due_ts)
        summary = t.get("summary", "(无标题)")
        status = t.get("status", "todo")
        guid = t.get("guid", "")

        days_info = ""
        if dt:
            delta = (dt.date() - now.date()).days
            due_str = dt.strftime('%m/%d')
            if delta < 0:
                days_info = f"⚠️ {due_str} (逾期 {-delta} 天)"
            elif delta == 0:
                days_info = f"🔴 {due_str}"
            elif delta <= 3:
                days_info = f"🟡 {due_str}"
            else:
                days_info = f"📅 {due_str}"

            entry = {"summary": summary, "guid": guid, "due": dt, "days_info": days_info, "overdue_days": -delta if delta < 0 else None}
            if delta < 0:
                overdue.append(entry)
            else:
                upcoming.append(entry)
        else:
            no_due.append({"summary": summary, "guid": guid, "due": None, "days_info": "📋 无期限", "overdue_days": None})

    # 排序：无期限放最后，其他按截止日期排序
    upcoming.sort(key=lambda x: x["due"] or datetime.max)
    overdue.sort(key=lambda x: x["overdue_days"] or 0, reverse=True)

    if overdue:
        print("## ⚠️ 逾期任务")
        for i, t in enumerate(overdue, 1):
            print(f"  {i}. {t['summary']} | {t['days_info']} | `{t['guid'][:8]}`")

    if upcoming:
        print("## 📅 即将到期")
        for i, t in enumerate(upcoming, 1):
            print(f"  {i}. {t['summary']} | {t['days_info']} | `{t['guid'][:8]}`")

    if no_due:
        print("## 📋 无期限")
        for i, t in enumerate(no_due, 1):
            print(f"  {i}. {t['summary']} | `{t['guid'][:8]}`")

    print(f"\n共 {len(tasks)} 个任务（逾期 {len(overdue)}，到期 {len(upcoming)}，无期限 {len(no_due)}）")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--completed", type=lambda x: x == "true", default=False)
    parser.add_argument("--show-all", action="store_true")
    args = parser.parse_args()

    tasks = fetch_tasks(completed=args.completed)
    if not args.show_all:
        # 默认只显示前20条摘要
        print(f"# 共获取 {len(tasks)} 个任务")
        # 按类型打印摘要
        todo = [t for t in tasks if t.get("status") == "todo"]
        done = [t for t in tasks if t.get("status") == "done"]
        print(f"# 未完成: {len(todo)}, 已完成: {len(done)}")
        render_tasks(tasks[:20], show_completed=args.completed)
        if len(tasks) > 20:
            print(f"# ... 还有 {len(tasks) - 20} 条")
    else:
        render_tasks(tasks, show_completed=args.completed)
