#!/usr/bin/env python3
"""
feishu-task: batch_delete.py
批量删除任务
- 串行执行，禁止并行
- 成功判断: {"code": 0}
- lark-cli tasks delete 内置 --page-delay 200ms 防限流
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta


SH_TZ = timezone(timedelta(hours=8))


def fmt_due(ts):
    if not ts or ts == "0":
        return "无期限"
    return datetime.fromtimestamp(int(ts) / 1000, tz=SH_TZ).strftime("%Y-%m-%d")


def fetch_task_summary(guid):
    """通过 tasks list 模糊查找任务标题（completed=false 和 true 都查）"""
    for completed in [False, True]:
        result = subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", json.dumps({"completed": completed, "page_size": 100}),
             "--format", "json", "--page-all"],
            capture_output=True, text=True
        )
        data = _parse_json(result.stdout)
        if data and data.get("code") == 0:
            for t in data.get("data", {}).get("items", []):
                if t.get("guid") == guid:
                    return t
    return {"guid": guid, "summary": f"(guid={guid})", "due": {}}


def delete_single(guid, dry_run=True):
    """删除单个任务"""
    params_file = "./batch_delete_params.json"
    with open(params_file, "w") as f:
        json.dump({"task_guid": guid}, f)

    cmd = ["lark-cli", "task", "tasks", "delete",
           "--params", f"@{params_file}", "--yes"]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(params_file)

    data = _parse_json(result.stdout + result.stderr)
    if data:
        return data.get("code") == 0
    return False


def _parse_json(stdout):
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith("[") or line == "}":
                continue
            try:
                brace_start = line.find("{")
                if brace_start >= 0:
                    return json.loads(line[brace_start:])
            except json.JSONDecodeError:
                continue
    return None


def main():
    parser = argparse.ArgumentParser(description="批量删除任务")
    parser.add_argument("--task-guid", action="append", default=[], dest="guids",
                       help="指定任务 guid（可多次指定）")
    parser.add_argument("--yes", action="store_true",
                       help="跳过确认，直接删除")
    args = parser.parse_args()

    if not args.guids:
        print("❌ 需指定至少一个 --task-guid", file=sys.stderr)
        sys.exit(1)

    # 先查标题（用于展示）
    tasks = []
    for g in args.guids:
        t = fetch_task_summary(g)
        t["guid"] = g
        tasks.append(t)

    print(f"🗑️  将删除 {len(tasks)} 个任务:")
    for t in tasks:
        due = fmt_due(t.get("due", {}).get("timestamp", "0"))
        print(f"  [{t['guid']}] {t.get('summary','(无标题)')} 截止 {due}")

    if not args.yes:
        confirm = input(f"\n⚠️ 确认删除这 {len(tasks)} 个任务？此操作不可恢复！(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消")
            return

    # Dry-run 预览
    print("\n🔍 Dry-run 预览:")
    ok_guids, fail_guids = [], []
    for t in tasks:
        guid = t["guid"]
        ok = delete_single(guid, dry_run=True)
        (ok_guids if ok else fail_guids).append(guid)
        print(f"  {'✅' if ok else '❌'} {guid}")

    if fail_guids:
        print(f"\n⚠️ {len(fail_guids)} 个任务可能不存在，跳过")

    # 正式执行（串行）
    print("\n🚀 开始批量删除:")
    done, failed = [], []
    for guid in ok_guids:
        ok = delete_single(guid, dry_run=False)
        if ok:
            done.append(guid)
            print(f"  ✅ {guid}")
        else:
            failed.append(guid)
            print(f"  ❌ {guid}")
        time.sleep(0.2)

    print(f"\n📊 删除 {len(done)}/{len(ok_guids)} 个" +
          (f"，失败 {len(failed)} 个" if failed else ""))


if __name__ == "__main__":
    main()
