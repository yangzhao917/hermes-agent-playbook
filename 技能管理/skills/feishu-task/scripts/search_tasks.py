#!/usr/bin/env python3
"""搜索飞书任务（+search 命令）"""
import subprocess, json, sys
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))

def search_tasks(query: str, completed: bool = None, due_range: str = None):
    cmd = [
        "lark-cli", "task", "+search",
        "--query", query,
        "--format", "json",
        "--page-all",
        "--page-limit", "40"
    ]
    if completed is True:
        cmd.append("--completed")
    elif completed is False:
        cmd.extend(["--completed", "false"])
    # 注：+search --completed false 的语法不支持，见下方 workaround

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
    except:
        # fallback：去掉 --completed 参数
        cmd = [c for c in cmd if c not in ["--completed", "false"]]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

    if not data.get("ok"):
        return [], data.get("msg", "搜索失败")

    items = data.get("data", {}).get("items", [])
    return items, None


def render_search_results(items, query):
    if not items:
        print(f"没找到「{query}」相关任务")
        return

    print(f"找到 {len(items)} 个相关任务：\n")
    for i, t in enumerate(items, 1):
        summary = t.get("summary", "(无标题)")
        status = t.get("status", "unknown")
        due_at = t.get("due_at") or (t.get("due", {}).get("timestamp") if t.get("due") else None)

        if due_at:
            try:
                if isinstance(due_at, str):
                    if "T" in due_at:
                        dt = datetime.fromisoformat(due_at[:19]).replace(tzinfo=SH_TZ)
                    elif "-" in due_at or "/" in due_at:
                        # 格式: "2026-04-17 08:00:00" 或 "2026/04/17 08:00:00"
                        clean = due_at.split(".")[0].strip()
                        dt = datetime.fromisoformat(clean).replace(tzinfo=SH_TZ)
                    else:
                        dt = datetime.fromtimestamp(int(due_at)/1000, tz=SH_TZ)
                else:
                    dt = datetime.fromtimestamp(int(due_at)/1000, tz=SH_TZ)
                due_str = dt.strftime("%m/%d")
            except:
                due_str = "未知"
        else:
            due_str = "无期限"

        status_icon = "✅" if status == "done" else "⬜"
        print(f"  {i}. {status_icon} {summary}")
        print(f"     截止: {due_str}  |  状态: {status}  |  `{t.get('guid','')[:8]}`")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    items, err = search_tasks(args.query)
    if err:
        print(f"❌ {err}")
        sys.exit(1)
    render_search_results(items, args.query)
