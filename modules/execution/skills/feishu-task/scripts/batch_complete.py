#!/usr/bin/env python3
"""
feishu-task: batch_complete.py
批量完成任务（指定 guid 或自动找已逾期任务）
- lark-cli +complete --dry-run 内置预览
- 串行执行，禁止并行
- 成功判断: {"ok": true}
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta


SH_TZ = timezone(timedelta(hours=8))
USER_OPEN_ID = "ou_5b875f5ec5752b06832bb240ad482ec0"


def fmt_due(ts):
    if not ts or ts == "0":
        return "无期限"
    return datetime.fromtimestamp(int(ts) / 1000, tz=SH_TZ).strftime("%Y-%m-%d")


def fetch_tasks_by_guids(guids):
    """根据 guid 列表精确拉取任务（用于 --overdue 后的补充校验）"""
    results = []
    for g in guids:
        result = subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", json.dumps({"completed": False, "page_size": 100}),
             "--format", "json", "--page-all"],
            capture_output=True, text=True
        )
        data = _parse_json(result.stdout)
        if data and data.get("code") == 0:
            for t in data.get("data", {}).get("items", []):
                if t.get("guid") == g:
                    results.append(t)
    return results


def fetch_overdue_tasks(days=0):
    """获取已逾期任务（status=todo 且 due.timestamp < now 或 超过 days 天）"""
    now_ms = int(datetime.now(SH_TZ).timestamp() * 1000)
    overdue_threshold = now_ms - days * 24 * 60 * 60 * 1000 if days else 0

    all_tasks = []
    page_token = None

    while True:
        params = {"completed": False, "page_size": 100}
        if page_token:
            params["page_token"] = page_token

        result = subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", json.dumps(params),
             "--format", "json", "--page-all"],
            capture_output=True, text=True
        )
        data = _parse_json(result.stdout)
        if not data or data.get("code") != 0:
            break

        items = data.get("data", {}).get("items", [])
        for t in items:
            if t.get("status") != "todo":
                continue
            due_ts = t.get("due", {}).get("timestamp", "0")
            if not due_ts or due_ts == "0":
                continue
            due_ms = int(due_ts)
            if days > 0:
                # 超过 N 天未完成也算逾期
                if due_ms < overdue_threshold:
                    all_tasks.append(t)
            else:
                # 严格逾期：截止时间 < 当前时间
                if due_ms < now_ms:
                    all_tasks.append(t)

        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token")
        if not has_more or not page_token:
            break

    return all_tasks


def complete_single(guid, dry_run=True):
    """完成单个任务（dry-run 或正式）"""
    cmd = ["lark-cli", "task", "+complete", "--task-id", guid]
    if dry_run:
        cmd.append("--dry-run")
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = _parse_json(result.stdout + result.stderr)
    if data:
        if dry_run:
            return data.get("ok") is True or data.get("code") == 0
        return data.get("ok") is True
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
    parser = argparse.ArgumentParser(description="批量完成任务")
    parser.add_argument("--task-id", action="append", default=[], dest="task_ids",
                       help="指定任务 guid（可多次指定）")
    parser.add_argument("--overdue", action="store_true",
                       help="自动找出已逾期任务")
    parser.add_argument("--days", type=int, default=0,
                       help="超过 N 天未完成也算逾期（配合 --overdue 使用）")
    parser.add_argument("--yes", action="store_true",
                       help="跳过确认，直接执行")
    args = parser.parse_args()

    # 发现任务
    if args.overdue:
        tasks = fetch_overdue_tasks(days=args.days)
        mode = "已逾期"
    elif args.task_ids:
        tasks = [{"guid": g, "summary": f"guid={g}", "due": {}}
                 for g in args.task_ids]
        mode = "指定"
    else:
        print("❌ 需指定 --task-id 或 --overdue", file=sys.stderr)
        sys.exit(1)

    if not tasks:
        print(f"✅ 没有{mode}任务需要完成")
        return

    print(f"📋 将完成 {len(tasks)} 个任务:")
    for t in tasks:
        due = fmt_due(t.get("due", {}).get("timestamp", "0"))
        print(f"  [{t['guid']}] {t.get('summary','(无标题)')} 截止 {due}")

    if not args.yes:
        confirm = input(f"\n确认完成这 {len(tasks)} 个任务？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消")
            return

    # Dry-run 预览（先跑一遍确保都能找到）
    print("\n🔍 Dry-run 预览:")
    ok_guids, fail_guids = [], []
    for t in tasks:
        guid = t["guid"]
        ok = complete_single(guid, dry_run=True)
        (ok_guids if ok else fail_guids).append(guid)
        print(f"  {'✅' if ok else '❌'} {guid}")

    if fail_guids:
        print(f"\n⚠️ {len(fail_guids)} 个任务可能不存在或已删除，跳过这些")

    # 正式执行（串行，每次单独调用）
    print("\n🚀 开始批量完成:")
    done, failed = [], []
    for guid in ok_guids:
        ok = complete_single(guid, dry_run=False)
        if ok:
            done.append(guid)
            print(f"  ✅ {guid}")
        else:
            failed.append(guid)
            print(f"  ❌ {guid}")
        time.sleep(0.2)  # 防限流

    print(f"\n📊 完成 {len(done)}/{len(ok_guids)} 个" +
          (f"，失败 {len(failed)} 个" if failed else ""))


if __name__ == "__main__":
    main()
