#!/usr/bin/env python3
"""
每日复盘总结生成
在飞书创建或覆盖当天复盘文档（幂等）。
依赖: lark-cli
"""
import subprocess
import json
import sys
from datetime import datetime, timezone, timedelta

FEISHU_FOLDER = "HermesAgent/每日复盘/"


def get_cst_now():
    return datetime.now(timezone(timedelta(hours=8)))


def get_date_range(days_offset=0):
    """返回 (date_str, start_iso, end_iso)，CST 时区。"""
    dt = get_cst_now() + timedelta(days=days_offset)
    date_str = dt.strftime("%Y-%m-%d")
    return date_str, f"{date_str}T00:00:00+08:00", f"{date_str}T23:59:59+08:00"


def get_folder_token(folder_name: str, parent_token: str = None) -> str | None:
    params = {} if not parent_token else {"folder_token": parent_token}
    cmd = ["lark-cli", "drive", "files", "list",
           "--params", json.dumps(params), "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        for item in data.get("data", {}).get("files", []):
            if item.get("name") == folder_name and item.get("type") == "folder":
                return item.get("token")
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def create_folder(name: str, parent_token: str = None) -> str | None:
    body = {"name": name, "folder_token": parent_token or ""}
    cmd = ["lark-cli", "drive", "files", "create_folder",
           "--data", json.dumps(body), "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data.get("data", {}).get("file", {}).get("token")
    except (json.JSONDecodeError, KeyError):
        return None


# HermesAgent 文件夹的真实父级（正确路径：HermesAgent/每日复盘/）
HERMES_PARENT_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"


def ensure_folder_structure() -> str | None:
    hermes_token = get_folder_token("HermesAgent", HERMES_PARENT_TOKEN)
    if not hermes_token:
        hermes_token = create_folder("HermesAgent", HERMES_PARENT_TOKEN)
        if not hermes_token:
            print("创建 HermesAgent 文件夹失败", file=sys.stderr)
            return None

    daily_token = get_folder_token("每日复盘", hermes_token)
    if not daily_token:
        daily_token = create_folder("每日复盘", hermes_token)
        if not daily_token:
            print("创建每日复盘文件夹失败", file=sys.stderr)
            return None

    return daily_token


def list_folder_files(folder_token: str) -> list:
    """列出 folder 内的所有文件，返回包含 token/name/type/create_time 的列表。"""
    params = {"folder_token": folder_token}
    cmd = ["lark-cli", "drive", "files", "list",
           "--params", json.dumps(params), "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("data", {}).get("files", [])
    except (json.JSONDecodeError, KeyError):
        return []


def find_doc_in_folder(folder_token: str, date_str: str) -> str | None:
    """在指定 folder 内找当天日期的文档，按创建时间降序返回最新的 token。"""
    files = list_folder_files(folder_token)
    matches = []
    for f in files:
        if f.get("type") in ("docx", "doc"):
            name = f.get("name", "")
            if date_str in name:
                # created_time 是 unix timestamp 字符串
                ct = int(f.get("created_time", 0))
                matches.append((ct, f.get("token"), name))
    if not matches:
        return None
    # 按 created_time 降序，取最新的
    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[0][1]


def create_doc(title: str, folder_token: str) -> str | None:
    result = subprocess.run(
        ["lark-cli", "docs", "+create",
         "--title", title, "--folder-token", folder_token, "--markdown", " "],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data.get("data", {}).get("doc_id")
    except (json.JSONDecodeError, KeyError):
        return None


def update_doc(doc_id: str, markdown: str):
    result = subprocess.run(
        ["lark-cli", "docs", "+update",
         "--doc", doc_id, "--markdown", markdown, "--mode", "overwrite"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def build_markdown(date_str: str) -> str:
    lines = [
        "## 📋 今日计划",
        "",
        "来源：昨日「明日待办」+ 今日新增计划",
        "",
        "| 时间 | 事项 | 备注 |",
        "|------|------|------|",
        "| - | - | - |",
        "",
        "## ✅ 今日完成",
        "",
        "| 完成 | 未完成 | 调整 |",
        "|------|--------|------|",
        "| - | - | - |",
        "",
        "## ⏰ 明日待办",
        "",
        "| 时间 | 事项 | 备注 |",
        "|------|------|------|",
        "| - | - | - |",
        "",
        "## 📌 待跟进",
        "",
        "🔴 紧急  🟡 一般  🟢 缓办",
        "",
        "## 📅 后续安排",
        "",
        "| 日期 | 事项 |",
        "|------|------|",
        "| - | - |",
        "",
        "## 💡 今日收获",
        "",
        "",
        "## ⚡ 今日感受",
        "",
    ]

    return "\n".join(lines)


def main():
    date_str = get_cst_now().strftime("%Y-%m-%d")
    print(f"正在生成 {date_str} 的复盘...", file=sys.stderr)

    folder_token = ensure_folder_structure()
    if not folder_token:
        print("无法获取文件夹，退出", file=sys.stderr)
        sys.exit(1)
    print(f"文件夹 token: {folder_token}", file=sys.stderr)

    # 在目标 folder 内找当天文档（按创建时间降序取最新）
    doc_id = find_doc_in_folder(folder_token, date_str)

    # 生成内容
    markdown = build_markdown(date_str)

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


if __name__ == "__main__":
    main()
