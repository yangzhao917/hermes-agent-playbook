#!/usr/bin/env python3
"""
daily-review v2: 每日复盘总结
- 微信版: 执行摘要（计划/完成/明日待办）
- 飞书文档: 深度复盘（完整记录）
"""

import subprocess
import re
import json
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CAL_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py"
TASK_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-task/scripts/list_tasks.py"
DRIVE_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py"  # placeholder


def get_cst_now():
    return datetime.now(SH_TZ)


def get_review_date(date_arg=None):
    """确定复盘日期：优先参数，其次今天"""
    if date_arg:
        return datetime.fromisoformat(date_arg).astimezone(SH_TZ)
    return get_cst_now()


def run_script(path, *args):
    cmd = ["python3", path] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


# ── 任务解析 ─────────────────────────────────────────────

def fetch_today_done(today_mmdd=None):
    """今日到期的已完成任务，返回 [summary, ...]"""
    out = run_script(TASK_LIST, "--status", "done")
    today = today_mmdd or get_cst_now().strftime("%m/%d")
    results = []
    for line in out.split("\n"):
        line = line.strip()
        if not line or line.startswith("✅") or "暂无" in line:
            continue
        # "  ✓ 标题  截止 MM/DD"
        m = re.match(r"^✓\s+(.+?)\s+截止\s+(\d{2}/\d{2})$", line)
        if m and m.group(2) == today:
            results.append(m.group(1).strip())
    return results


def fetch_today_todo(today_mmdd=None):
    """今日到期的未完成任务，返回 [summary, ...]"""
    out = run_script(TASK_LIST, "--status", "todo")
    today = today_mmdd or get_cst_now().strftime("%m/%d")
    results = []
    for line in out.split("\n"):
        line = line.strip()
        if not line or line.startswith("📋") or "暂无" in line:
            continue
        # "  ○ 标题  截止 MM/DD"
        m = re.match(r"^○\s+(.+?)\s+截止\s+(\d{2}/\d{2})$", line)
        if m and m.group(2) == today:
            results.append(m.group(1).strip())
    return results


def fetch_tomorrow_todo(tomorrow_mmdd=None):
    """明日到期的未完成任务，返回 [summary, ...]"""
    out = run_script(TASK_LIST, "--status", "todo")
    tomorrow = tomorrow_mmdd or (get_cst_now() + timedelta(days=1)).strftime("%m/%d")
    results = []
    for line in out.split("\n"):
        line = line.strip()
        if not line or line.startswith("📋") or "暂无" in line:
            continue
        m = re.match(r"^○\s+(.+?)\s+截止\s+(\d{2}/\d{2})$", line)
        if m and m.group(2) == tomorrow:
            results.append(m.group(1).strip())
    return results


# ── 日历解析 ─────────────────────────────────────────────

def fetch_today_calendar(date_str):
    """今日日历事件，返回 [(time_str, summary), ...]"""
    out = run_script(CAL_LIST, "--date", date_str)
    results = []
    for line in out.split("\n"):
        line = line.strip()
        if not line or "暂无" in line:
            continue
        # "  05/22 16:20 ~ 05/22 19:23  标题"
        m = re.match(
            r"^\d{2}/\d{2}\s+(\d{2}:\d{2})\s+~\s+\d{2}/\d{2}\s+\d{2}:\d{2}\s+(.+)$",
            line,
        )
        if m:
            results.append((m.group(1), m.group(2).strip()))
    return results


# ── 飞书文档 ─────────────────────────────────────────────

HERMES_PARENT_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"


def find_doc(title, folder_token):
    """在文件夹中查找同名文档，返回 doc_id 或 None"""
    params = {"folder_token": folder_token}
    result = subprocess.run(
        ["lark-cli", "drive", "files", "list",
         "--params", json.dumps(params), "--format", "json"],
        capture_output=True, text=True
    )
    data = _parse_json(result.stdout)
    if not data:
        return None
    for f in data.get("data", {}).get("files", []):
        if f.get("name") == title and f.get("type") in ("docx", "doc"):
            return f.get("token")
    return None


def create_doc(title, folder_token):
    """创建飞书文档，返回 doc_id 或 None"""
    result = subprocess.run(
        ["lark-cli", "docs", "+create",
         "--title", title, "--folder-token", folder_token, "--markdown", " "],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    data = _parse_json(result.stdout)
    if data:
        return data.get("data", {}).get("doc_id")
    return None


def update_doc(doc_id, markdown):
    """更新飞书文档内容"""
    result = subprocess.run(
        ["lark-cli", "docs", "+update",
         "--doc", doc_id, "--markdown", markdown, "--mode", "overwrite"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def _parse_json(stdout):
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            brace_start = line.find("{")
            if brace_start >= 0:
                return json.loads(line[brace_start:])
        except json.JSONDecodeError:
            continue
    return None


def get_folder_token(folder_name, parent_token=None):
    """获取或创建文件夹，返回 folder_token"""
    params = {} if not parent_token else {"folder_token": parent_token}
    result = subprocess.run(
        ["lark-cli", "drive", "files", "list",
         "--params", json.dumps(params), "--format", "json"],
        capture_output=True, text=True
    )
    data = _parse_json(result.stdout)
    if not data:
        return None
    for item in data.get("data", {}).get("files", []):
        if item.get("name") == folder_name and item.get("type") == "folder":
            return item.get("token")
    # 不存在则创建
    body = {"name": folder_name, "folder_token": parent_token or ""}
    res = subprocess.run(
        ["lark-cli", "drive", "files", "create_folder",
         "--data", json.dumps(body), "--format", "json"],
        capture_output=True, text=True
    )
    d = _parse_json(res.stdout)
    if d:
        return d.get("data", {}).get("file", {}).get("token")
    return None


def ensure_review_folder():
    """确保 HermesAgent/每日复盘 文件夹存在，返回 folder_token"""
    hermes_tok = get_folder_token("HermesAgent", HERMES_PARENT_TOKEN)
    if not hermes_tok:
        return None
    daily_tok = get_folder_token("每日复盘", hermes_tok)
    if not daily_tok:
        return None
    return daily_tok


# ── Markdown 构建 ─────────────────────────────────────────

def build_table(rows, cols):
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for row in rows:
        cells = [str(c) if c else "-" for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_feishu_doc(date_str, done, tomorrow_todo, calendar_ev, review_date, harvest=None):
    """构建飞书文档完整 Markdown"""
    lines = [f"# {date_str} 总结", ""]

    # 📍 今日日历
    lines.append("## 📍 今日日历")
    if calendar_ev:
        for t, s in calendar_ev:
            lines.append(f"- {t} {s}")
    else:
        lines.append("（暂无）")
    lines.append("")

    # ✅ 今日完成
    lines.append("## ✅ 今日完成")
    if done:
        for s in done:
            lines.append(f"- {s}")
    else:
        lines.append("（暂无）")
    lines.append("")

    # 💡 今日收获
    lines.append("## 💡 今日收获")
    if harvest:
        lines.append(harvest)
    else:
        lines.append("（暂无）")
    lines.append("")

    # ⏰ 明日待办
    lines.append("## ⏰ 明日待办")
    if tomorrow_todo:
        for s in tomorrow_todo:
            lines.append(f"- {s}")
    else:
        lines.append("（暂无）")
    lines.append("")

    # 🔜 后续跟进
    lines.append("## 🔜 后续跟进")
    lines.append("（暂无）")

    return "\n".join(lines)


def build_wechat_msg(date_str, done, today_todo, tomorrow_todo, doc_title, doc_url, review_date, calendar_ev):
    """构建微信推送文本"""
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    day_name = day_names[review_date.weekday()]

    lines = [f"📌 {date_str} {day_name}（昨日）", ""]

    # 今日计划 = 日历事件 + 今日到期任务
    lines.append("📍 昨日日程")
    has_plan = False
    if calendar_ev:
        for t, s in calendar_ev:
            lines.append(f"  📅 {t} {s}")
            has_plan = True
    if today_todo:
        for s in today_todo:
            lines.append(f"  📋 {s}")
            has_plan = True
    if not has_plan:
        lines.append("  （暂无）")
    lines.append("")

    # 今日完成
    lines.append("✅ 今日完成")
    if done:
        for s in done:
            lines.append(f"  ✓ {s}")
    else:
        lines.append("  （暂无）")
    lines.append("")

    # 明日待办
    lines.append("⏰ 明日待办")
    if tomorrow_todo:
        for s in tomorrow_todo:
            lines.append(f"  → {s}")
    else:
        lines.append("  （暂无）")
    lines.append("")

    lines.append(f"📄 文档链接：[HermesAgent/每日复盘/{doc_title}]({doc_url})")

    return "\n".join(lines)


# ── 主流程 ───────────────────────────────────────────────

def main():
    import argparse as _argparse
    _parser = _argparse.ArgumentParser()
    _parser.add_argument("--date", type=str, help="复盘日期 YYYY-MM-DD（默认昨天）")
    _args, _ = _parser.parse_known_args()

    review_date = get_review_date(_args.date)
    date_str = review_date.strftime("%Y-%m-%d")
    tomorrow_date = (review_date + timedelta(days=1)).strftime("%m/%d")
    today_mmdd = review_date.strftime("%m/%d")

    # 1. 拉数据
    done = fetch_today_done(today_mmdd)
    today_todo = fetch_today_todo(today_mmdd)
    tomorrow_todo = fetch_tomorrow_todo(tomorrow_date)
    calendar_ev = fetch_today_calendar(date_str)

    # 2. 飞书文档（幂等：同日覆盖）
    folder_tok = ensure_review_folder()
    doc_title = f"{date_str}-每日复盘"
    doc_url = ""

    if folder_tok:
        doc_id = find_doc(doc_title, folder_tok)
        if not doc_id:
            doc_id = create_doc(doc_title, folder_tok)
        if doc_id:
            markdown = build_feishu_doc(date_str, done,
                                        tomorrow_todo, calendar_ev, review_date)
            update_doc(doc_id, markdown)
            doc_url = f"https://feishu.cn/docx/{doc_id}"

    # 3. 微信推送（stdout）
    wechat = build_wechat_msg(date_str, done, today_todo, tomorrow_todo, doc_title, doc_url, review_date, calendar_ev)
    print(wechat)


if __name__ == "__main__":
    main()
