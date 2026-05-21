#!/usr/bin/env python3
"""
每日复盘总结生成 — cron wrapper script
由 install.py 安装到 ~/.hermes/scripts/daily_review.py
"""
import subprocess
import json
import sys
from pathlib import Path

# 共享 lib 在 skills/lib/
sys.path.insert(0, str(Path(__file__).parent / "lib"))  # lib: ~/.hermes/scripts/lib/

from cron import get_cst_now, get_date_range, lark_calendar_agenda, format_event_time

FEISHU_FOLDER = "{{FEISHU_FOLDER}}"  # 安装时自动替换


def get_today_str():
    return get_cst_now().strftime("%Y-%m-%d")


def get_folder_token(folder_name: str, parent_token: str = None) -> str | None:
    cmd = ["lark-cli", "drive", "+list", "--format", "json"]
    if parent_token:
        cmd += ["--folder-token", parent_token]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        items = json.loads(result.stdout)
        for item in items:
            if item.get("name") == folder_name and item.get("type") == "folder":
                return item.get("token")
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def create_folder(name: str, parent_token: str = None) -> str | None:
    cmd = ["lark-cli", "drive", "+create-folder", "--name", name, "--format", "json"]
    if parent_token:
        cmd += ["--folder-token", parent_token]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data.get("token") or data.get("folder_token")
    except (json.JSONDecodeError, KeyError):
        return None


def ensure_folder_structure() -> str | None:
    hermes_token = get_folder_token("hermesAgent")
    if not hermes_token:
        hermes_token = create_folder("hermesAgent")
        if not hermes_token:
            print("创建 hermesAgent 文件夹失败", file=sys.stderr)
            return None

    daily_token = get_folder_token("每日复盘", hermes_token)
    if not daily_token:
        daily_token = create_folder("每日复盘", hermes_token)
        if not daily_token:
            print("创建每日复盘文件夹失败", file=sys.stderr)
            return None

    return daily_token


def search_docs(query: str, folder_token: str = None) -> list:
    cmd = ["lark-cli", "docs", "+search", "--query", query,
           "--format", "json", "--doc-types", "docx"]
    if folder_token:
        cmd += ["--folder-tokens", folder_token]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def create_doc(title: str, folder_token: str) -> str | None:
    result = subprocess.run(
        ["lark-cli", "docs", "+create",
         "--title", title, "--folder-token", folder_token, "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data.get("doc_id") or data.get("document", {}).get("document_id")
    except (json.JSONDecodeError, KeyError):
        return None


def update_doc(doc_id: str, markdown: str):
    result = subprocess.run(
        ["lark-cli", "docs", "+update",
         "--doc", doc_id, "--markdown", markdown, "--mode", "overwrite"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def build_markdown(date_str: str, events: list) -> str:
    event_lines = []
    if events:
        for ev in events:
            title = ev.get("summary") or ev.get("title") or "无标题"
            time_str = format_event_time(ev.get("start") or "")
            event_lines.append(f"- {time_str} {title}" if time_str else f"- {title}")

    lines = [
        f"# {date_str} 复盘总结",
        "",
        "## 📋 计划事项（必须）",
        "",
        "来源：昨日「明日待办」+ 今日新增计划",
        "",
        "| 时间 | 事项 | 备注 |",
        "|------|------|------|",
        "| - | - | - |",
        "",
        "## ✅ 完成情况（必须）",
        "",
        "| 完成 | 未完成 | 调整 |",
        "|------|--------|------|",
        "| - | - | - |",
        "",
        "## ⏰ 明日待办（必须）",
        "",
        "| 时间 | 事项 | 备注 |",
        "|------|------|------|",
        "| - | - | - |",
        "",
        "## 📌 待跟进",
        "",
        "带紧迫度标注（🔴🟡🟢）",
        "",
        "## 📅 后续安排（建议）",
        "",
        "| 日期 | 事项 |",
        "|------|------|",
        "| - | - |",
        "",
        "## 💡 今天学到的（建议）",
        "",
        "",
        "## ⚡ 今日高光/感受（选填）",
        "",
    ]

    if event_lines:
        lines.extend(["", "---", "", "### 今日日历事件"])
        lines.extend(event_lines)

    return "\n".join(lines)


def main():
    date_str = get_today_str()
    print(f"正在生成 {date_str} 的复盘...", file=sys.stderr)

    folder_token = ensure_folder_structure()
    if not folder_token:
        print("无法获取文件夹，退出", file=sys.stderr)
        sys.exit(1)
    print(f"文件夹 token: {folder_token}", file=sys.stderr)

    existing = search_docs(date_str, folder_token)
    doc_id = None
    for doc in existing:
        title = doc.get("title", "")
        if date_str in title:
            doc_id = (doc.get("doc_id") or doc.get("document_id")
                      or doc.get("document", {}).get("document_id"))
            break

    _, today_start, today_end = get_date_range(0)
    events = lark_calendar_agenda(today_start, today_end)

    markdown = build_markdown(date_str, events)

    if doc_id:
        print(f"找到已有文档: {doc_id}，将覆盖内容", file=sys.stderr)
    else:
        doc_title = f"{date_str}-复盘总结"
        doc_id = create_doc(doc_title, folder_token)
        if not doc_id:
            print("创建文档失败", file=sys.stderr)
            sys.exit(1)
        print(f"已创建新文档: {doc_id}", file=sys.stderr)

    ok = update_doc(doc_id, markdown)
    if not ok:
        print("更新文档失败", file=sys.stderr)
        sys.exit(1)

    print(f"文档已保存: {doc_id}", file=sys.stderr)

    print(f"\n✅ {date_str} 复盘已完成")
    print(f"\n飞书文档已更新: {FEISHU_FOLDER}{date_str}-复盘总结")
    if events:
        print("\n今日日历参考:")
        for ev in events:
            title = ev.get("summary") or ev.get("title") or "无标题"
            print(f"  • {title}")
    else:
        print("\n（今日无日历事件）")


if __name__ == "__main__":
    main()
