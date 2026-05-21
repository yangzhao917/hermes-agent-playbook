#!/usr/bin/env python3
"""批量完成任务（串行，带进度反馈和限流重试）"""
import subprocess, json, sys, time
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))

def complete_one(guid: str, retry: int = 1) -> bool:
    """完成单个任务，失败重试一次"""
    for attempt in range(retry + 1):
        result = subprocess.run(
            ["lark-cli", "task", "+complete", "--task-id", guid, "--format", "json"],
            capture_output=True, text=True
        )
        try:
            data = json.loads(result.stdout)
        except:
            if attempt < retry:
                time.sleep(3)
                continue
            return False
        if data.get("ok"):
            return True
        if attempt < retry:
            time.sleep(3)
    return False

def batch_complete(guids: list, confirm: bool = True):
    if not guids:
        print("没有要完成的任务")
        return

    print(f"即将完成 {len(guids)} 个任务：")
    for i, guid in enumerate(guids, 1):
        print(f"  {i}. `{guid[:8]}`")
    if confirm:
        print("\n确认执行？（y/N）")
        if input().strip().lower() != "y":
            print("已取消")
            return

    ok_count = 0
    fail_count = 0
    for i, guid in enumerate(guids, 1):
        ok = complete_one(guid)
        if ok:
            ok_count += 1
            print(".", end="", flush=True)
        else:
            fail_count += 1
            print(f"\n❌ 失败 [{i}/{len(guids)}]: {guid[:8]}")
        if i % 10 == 0:
            print(f" [{i}/{len(guids)}]")
        time.sleep(0.2)  # 限流缓冲

    print(f"\n\n✅ 成功: {ok_count}  ❌ 失败: {fail_count}  共 {len(guids)} 个")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--overdue-only", action="store_true", help="只清理已逾期的任务")
    parser.add_argument("--all", action="store_true", help="清理所有未完成任务")
    parser.add_argument("--no-confirm", action="store_true")
    args = parser.parse_args()

    if not (args.overdue_only or args.all):
        print("请指定 --overdue-only 或 --all")
        sys.exit(1)

    # 获取所有未完成任务
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
        all_items.extend(data.get("data", {}).get("items", []))
        if not data.get("data", {}).get("has_more"):
            break
        page_token = data.get("data", {}).get("page_token")
        if not page_token:
            break

    now = datetime.now(tz=SH_TZ)
    today = now.date()

    if args.overdue_only:
        guids = []
        for t in all_items:
            due_ts = t.get("due", {}).get("timestamp", "0") if t.get("due") else "0"
            if due_ts and due_ts != "0":
                dt = datetime.fromtimestamp(int(due_ts)/1000, tz=SH_TZ)
                if dt.date() < today:
                    guids.append(t["guid"])
        batch_complete(guids, confirm=not args.no_confirm)
    else:
        guids = [t["guid"] for t in all_items]
        batch_complete(guids, confirm=not args.no_confirm)
