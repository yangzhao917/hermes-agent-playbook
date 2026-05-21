#!/usr/bin/env python3
"""
每日复盘总结生成 — cron wrapper script
由 install.py 安装到 ~/.hermes/scripts/daily_review.py

依赖: lark-cli

文档创建流程:
1. 确保文件夹 hermesAgent/每日复盘/ 存在（自动创建）
2. 搜索当天是否已有文档
3. 有 → 覆盖内容; 无 → 创建新文档
4. 输出摘要供 deliver 使用
"""
import subprocess
import json
import sys
from datetime import datetime, timezone, timedelta

FEISHU_FOLDER = "{{FEISHU_FOLDER}}"  # 安装时自动替换

def get_today_str():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")

def api(method, path, data=None):
    """调用 lark-cli API。"""
    cmd = ["lark-cli", "api", method, path]
    if data:
        cmd += ["--data", json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

def get_folder_token(folder_name: str, parent_token: str = None) -> str | None:
    """列出文件夹内容，返回同名文件夹的 token。"""
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
    """创建文件夹，返回 folder_token。"""
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
    """确保 hermesAgent/每日复盘/ 文件夹存在，返回最终 folder_token。"""
    # 尝试逐级获取或创建
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
    """搜索文档。"""
    cmd = ["lark-cli", "docs", "+search", "--query", query, "--format", "json", "--doc-types", "docx"]
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
    """创建文档，返回 doc_id。"""
    result = subprocess.run(
        ["lark-cli", "docs", "+create", "--title", title, "--folder-token", folder_token, "--format", "json"],
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
    """更新文档内容。"""
    result = subprocess.run(
        ["lark-cli", "docs", "+update", "--doc", doc_id, "--markdown", markdown, "--mode", "overwrite"],
        capture_output=True, text=True
    )
    return result.returncode == 0

def get_calendar_events() -> list:
    """获取今日日历事件（用于参考）。"""
    today = datetime.now(timezone(timedelta(hours=8)))
    date_str = today.strftime("%Y-%m-%d")
    start = f"{date_str}T00:00:00+08:00"
    end = f"{date_str}T23:59:59+08:00"
    result = subprocess.run(
        ["lark-cli", "calendar", "+agenda", "--start", start, "--end", end, "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

def build_markdown(date_str: str, events: list) -> str:
    """生成复盘文档的 Markdown 内容。"""
    event_lines = []
    if events:
        for ev in events:
            title = ev.get("summary") or ev.get("title") or "无标题"
            start_val = ev.get("start") or ""
            time_str = ""
            if start_val:
                try:
                    dt = datetime.fromisoformat(start_val.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M")
                except ValueError:
                    pass
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

    # 确保文件夹存在
    folder_token = ensure_folder_structure()
    if not folder_token:
        print("无法获取文件夹，退出", file=sys.stderr)
        sys.exit(1)
    print(f"文件夹 token: {folder_token}", file=sys.stderr)

    # 搜索当天文档
    existing = search_docs(date_str, folder_token)
    doc_id = None
    for doc in existing:
        title = doc.get("title", "")
        if date_str in title:
            doc_id = doc.get("doc_id") or doc.get("document_id") or doc.get("document", {}).get("document_id")
            break

    # 获取日历参考
    events = get_calendar_events()

    # 生成内容
    markdown = build_markdown(date_str, events)

    # 创建或更新文档
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

    # 输出摘要（供 deliver 使用）
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
