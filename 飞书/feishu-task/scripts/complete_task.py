#!/usr/bin/env python3
"""完成任务，支持模糊匹配任务名"""
import subprocess, json, sys, difflib
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))

def get_my_open_id():
    result = subprocess.run(
        ["lark-cli", "contact", "+search-user", "--user-ids", "me", "--format", "json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    users = data.get("data", {}).get("users", [])
    return users[0].get("open_id") if users else None

def fetch_todo_tasks():
    all_items = []
    page_token = None
    while True:
        params = {"completed": False, "page_size": 100}
        if page_token:
            params["page_token"] = page_token
        result = subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", json.dumps(params), "--format", "json"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        items = data.get("data", {}).get("items", [])
        all_items.extend(items)
        if not data.get("data", {}).get("has_more"):
            break
        page_token = data.get("data", {}).get("page_token")
        if not page_token:
            break
    return all_items

def fuzzy_match(query: str, tasks, threshold: int = 60):
    """返回匹配度最高的任务列表"""
    names = [(t["guid"], t.get("summary", "")) for t in tasks]
    scores = []
    for guid, name in names:
        ratio = difflib.SequenceMatcher(None, query, name).ratio()
        if ratio >= threshold / 100:
            scores.append((ratio, guid, name))
    scores.sort(reverse=True)
    return scores

def complete_task(guid: str):
    result = subprocess.run(
        ["lark-cli", "task", "+complete", "--task-id", guid, "--format", "json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data.get("ok", False)

def render_task_choice(tasks_map, scores):
    print(f"\n找到以下匹配任务（模糊匹配度从高到低）：")
    for i, (ratio, guid, name) in enumerate(scores[:5], 1):
        t = tasks_map[guid]
        due_ts = t.get("due", {}).get("timestamp", "0") if t.get("due") else "0"
        if due_ts and due_ts != "0":
            dt = datetime.fromtimestamp(int(due_ts)/1000, tz=SH_TZ)
            due_str = dt.strftime("%m/%d")
        else:
            due_str = "无期限"
        print(f"  {i}. [{int(ratio*100)}%] {name} | 截止: {due_str} | `{guid[:8]}`")
    return scores[:5]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="要完成的任务名称（支持模糊匹配）")
    parser.add_argument("--guid", help="直接指定 guid，跳过模糊匹配")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.guid:
        # 直接完成任务
        if args.dry_run:
            print(f"[dry-run] 本应完成任务: {args.guid}")
        else:
            ok = complete_task(args.guid)
            print(f"{'✅' if ok else '❌'} {'任务已完成' if ok else '完成任务失败'}")
        sys.exit(0)

    # 模糊匹配
    tasks = fetch_todo_tasks()
    tasks_map = {t["guid"]: t for t in tasks}
    scores = fuzzy_match(args.query, tasks)

    if not scores:
        print(f"❌ 没找到与「{args.query}」相近的任务（阈值60%）")
        print(f"   当前未完成任务共 {len(tasks)} 个")
        sys.exit(1)

    top = render_task_choice(tasks_map, scores)

    if len(top) == 1:
        chosen = top[0][1]
        print(f"\n🤖 自动选择最高匹配度({int(top[0][0]*100)}%)的任务")
    else:
        print(f"\n请确认要完成哪个任务（输入数字 1-{len(top)}）：")
        try:
            choice = int(input().strip())
            if choice < 1 or choice > len(top):
                print("无效选择")
                sys.exit(1)
            chosen = top[choice-1][1]
        except:
            print("无效输入")
            sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] 本应完成任务: {chosen}")
    else:
        ok = complete_task(chosen)
        print(f"{'✅' if ok else '❌'} {'任务已完成' if ok else '完成任务失败'}")
