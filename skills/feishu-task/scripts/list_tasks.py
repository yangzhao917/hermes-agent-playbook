#!/usr/bin/env python3
"""
feishu-task: list_tasks.py
查看飞书任务（未完成/已完成/全部）
- 自动翻页（page_size=100，--page-all）
- due.timestamp 是毫秒级
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta


SH_TZ = timezone(timedelta(hours=8))
USER_OPEN_ID = "ou_5b875f5ec5752b06832bb240ad482ec0"


def fmt_due(ts):
    """毫秒时间戳 → MM/DD"""
    if not ts or ts == "0":
        return "无期限"
    return datetime.fromtimestamp(int(ts) / 1000, tz=SH_TZ).strftime("%m/%d")


def fetch_tasks(completed):
    """获取任务列表（自动翻页）"""
    all_items = []
    page_token = None

    while True:
        params = {"completed": completed, "page_size": 100}
        if page_token:
            params["page_token"] = page_token

        result = subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", json.dumps(params),
             "--format", "json",
             "--page-all"],
            capture_output=True, text=True
        )

        data = _parse_json(result.stdout)
        if not data or data.get("code") != 0:
            break

        items = data.get("data", {}).get("items", [])
        all_items.extend(items)

        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token")
        if not has_more or not page_token:
            break

    return all_items


def _parse_json(stdout):
    """解析 lark-cli 的 --format json 输出
    - instance_view: 多行格式化 JSON → 整段解析
    - tasks list: 紧凑单行 JSON → 整段解析
    - 含 [deprecated] 前缀时 → 提取大括号内部分
    """
    text = stdout.strip()
    if not text:
        return None
    # 策略一：直接解析整段（处理多行格式 JSON）
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 策略二：跳过前缀行，找第一个 { 开始解析
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("[") or line == "}":
            continue
        try:
            # 跳过 [deprecated] 等前缀
            brace_start = line.find("{")
            if brace_start >= 0:
                return json.loads(line[brace_start:])
        except json.JSONDecodeError:
            continue
    return None



def main():
    parser = argparse.ArgumentParser(description="查看飞书任务")
    parser.add_argument("--status", choices=["todo", "done", "all"], default="todo",
                        help="todo=未完成, done=已完成, all=全部")
    args = parser.parse_args()

    if args.status == "todo":
        tasks = fetch_tasks(False)
    elif args.status == "done":
        tasks = fetch_tasks(True)
    else:
        # all: 合并
        todo = fetch_tasks(False)
        done = fetch_tasks(True)
        tasks = todo + done

    if not tasks:
        status_map = {"todo": "未完成", "done": "已完成", "all": "全部"}
        print(f"✅ {status_map[args.status]} 暂无任务")
        return

    # 按 status + due 排序
    def sort_key(t):
        s = t.get("status", "todo")
        due = t.get("due", {}).get("timestamp", "0")
        return (s != "todo", due)

    tasks.sort(key=sort_key)

    todo_tasks = [t for t in tasks if t.get("status") == "todo"]
    done_tasks = [t for t in tasks if t.get("status") == "done"]

    if args.status in ("todo", "all") and todo_tasks:
        print(f"📋 待办 ({len(todo_tasks)} 项)")
        for t in todo_tasks:
            due = fmt_due(t.get("due", {}).get("timestamp", "0"))
            summary = t.get("summary", "(无标题)")
            print(f"  ○ {summary}  截止 {due}")

    if args.status in ("done", "all") and done_tasks:
        print(f"\n✅ 已完成 ({len(done_tasks)} 项)")
        for t in done_tasks:
            due = fmt_due(t.get("due", {}).get("timestamp", "0"))
            summary = t.get("summary", "(无标题)")
            print(f"  ✓ {summary}  截止 {due}")


if __name__ == "__main__":
    main()
