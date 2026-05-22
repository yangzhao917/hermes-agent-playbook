#!/usr/bin/env python3
"""
每日复盘总结生成（完整版）
- 从飞书任务拉今日到期/已完成/明日待办
- 从飞书日历拉今日日程
- 生成文档并覆盖
依赖: lark-cli, feishu_calendar.py (OAuth user token)
"""
import subprocess
import json
import sys
import os
import urllib.request
from datetime import datetime, timezone, timedelta

FEISHU_FOLDER = "HermesAgent/每日复盘/"
TOKEN_FILE = os.path.expanduser("~/.hermes/feishu_user_token.json")


def get_cst_now():
    return datetime.now(timezone(timedelta(hours=8)))


def get_date_range(days_offset=0):
    """返回 (date_str, start_iso, end_iso)，CST 时区。"""
    dt = get_cst_now() + timedelta(days=days_offset)
    date_str = dt.strftime("%Y-%m-%d")
    return date_str, f"{date_str}T00:00:00+08:00", f"{date_str}T23:59:59+08:00"


# ─── 飞书任务 ───────────────────────────────────────────

def get_tasks(completed: bool) -> list:
    """获取任务列表。"""
    params = {"page_size": 50, "completed": completed}
    result = subprocess.run(
        ["lark-cli", "task", "tasks", "list",
         "--params", json.dumps(params), "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        if data.get("code") != 0:
            return []
        return data.get("data", {}).get("items", [])
    except json.JSONDecodeError:
        return []


def format_task_time(ts_ms: int | None) -> str:
    """毫秒时间戳 -> MM/DD"""
    if not ts_ms:
        return ""
    dt = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%m/%d")


def get_today_tasks() -> tuple:
    """返回 (今日计划, 今日完成, 明日待办, 待跟进) 四个列表，每个元素是 (时间, 事项, 备注)。"""
    today = get_cst_now().strftime("%Y-%m-%d")
    tomorrow = (get_cst_now() + timedelta(days=1)).strftime("%Y-%m-%d")
    today_dt = get_cst_now().date()
    tomorrow_dt = (get_cst_now() + timedelta(days=1)).date()

    incomplete = get_tasks(False)
    completed = get_tasks(True)

    today_plan, today_done, tomorrow_todo = [], [], []

    for t in incomplete:
        due = t.get("due", {})
        ts = due.get("timestamp") if due else None
        if not ts:
            continue
        dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone(timedelta(hours=8))).date()
        summary = t.get("summary", "无标题")
        if dt == today_dt:
            today_plan.append(("今日到期", summary, ""))
        elif dt == tomorrow_dt:
            tomorrow_todo.append(("明日到期", summary, ""))
        elif dt > today_dt:
            pass  # 跳过更远的

    # 已完成任务中找今天完成的
    done_summaries = set()
    for t in completed:
        due = t.get("due", {})
        ts = due.get("timestamp") if due else None
        if not ts:
            continue
        dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone(timedelta(hours=8))).date()
        summary = t.get("summary", "无标题")
        if dt == today_dt:
            today_done.append(("今日完成", summary, ""))
            done_summaries.add(summary)

    # 待跟进：今日计划中未完成的任务
    followup = [(time_label, summary, remark)
                for time_label, summary, remark in today_plan
                if summary not in done_summaries]

    return today_plan, today_done, tomorrow_todo, followup


# ─── 飞书日历 ───────────────────────────────────────────

def get_access_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    return data.get("access_token", "")


def get_primary_calendar_id(token: str) -> str | None:
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/calendar/v4/calendars?page_size=50",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        for cal in data.get("data", {}).get("calendar_list", []):
            if cal.get("type") == "primary":
                return cal.get("calendar_id")
    except Exception:
        pass
    return None


def get_calendar_events(token: str, cal_id: str, date_str: str) -> list:
    """返回 [(时间, 事项), ...]"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start_ts = int(datetime(dt.year, dt.month, dt.day, 0, 0, 0,
                            tzinfo=timezone(timedelta(hours=8))).timestamp())
    end_ts = int(datetime(dt.year, dt.month, dt.day, 23, 59, 59,
                          tzinfo=timezone(timedelta(hours=8))).timestamp())
    url = (f"https://open.feishu.cn/open-apis/calendar/v4/calendars/"
           f"{urllib.request.quote(cal_id)}/events"
           f"?page_size=50&start_time={start_ts}&end_time={end_ts}")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("data", {}).get("items", [])
    except Exception:
        return []


def format_event_time(ev: dict) -> str:
    st = ev.get("start_time", {})
    if "date" in st:
        return st["date"]
    ts = st.get("timestamp")
    if ts:
        dt = datetime.fromtimestamp(int(ts), tz=timezone(timedelta(hours=8)))
        return dt.strftime("%H:%M")
    return ""


def get_today_calendar() -> list:
    """返回 [(时间字符串, 事项), ...]"""
    token = get_access_token()
    if not token:
        return []
    cal_id = get_primary_calendar_id(token)
    if not cal_id:
        return []
    date_str = get_cst_now().strftime("%Y-%m-%d")
    events = get_calendar_events(token, cal_id, date_str)
    result = []
    for ev in events:
        if ev.get("status") == "cancelled":
            continue
        t = format_event_time(ev)
        name = ev.get("summary") or "无标题"
        loc = ev.get("location", {}).get("location", "")
        if loc:
            name = f"{name} @{loc}"
        result.append((t, name))
    return result


# ─── 飞书文档 ───────────────────────────────────────────

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


HERMES_PARENT_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"


def ensure_folder_structure() -> str | None:
    hermes_token = get_folder_token("HermesAgent", HERMES_PARENT_TOKEN)
    if not hermes_token:
        hermes_token = create_folder("HermesAgent", HERMES_PARENT_TOKEN)
        if not hermes_token:
            return None
    daily_token = get_folder_token("每日复盘", hermes_token)
    if not daily_token:
        daily_token = create_folder("每日复盘", hermes_token)
        if not daily_token:
            return None
    return daily_token


def list_folder_files(folder_token: str) -> list:
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
    files = list_folder_files(folder_token)
    matches = []
    for f in files:
        if f.get("type") in ("docx", "doc"):
            name = f.get("name", "")
            if date_str in name:
                ct = int(f.get("created_time", 0))
                matches.append((ct, f.get("token"), name))
    if not matches:
        return None
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


# ─── Markdown 生成 ───────────────────────────────────────

def build_table(rows: list, cols: list) -> str:
    """rows: [(cell, ...), ...]，cols: [列名, ...]"""
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join(["------"] * len(cols)) + "|"]
    for row in rows:
        cells = [str(c) if c else "-" for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_markdown(date_str: str, tasks_data: tuple, calendar_events: list) -> str:
    today_plan, today_done, tomorrow_todo, followup = tasks_data

    lines = []

    # 📋 今日计划
    if today_plan:
        lines.extend(["## 📋 今日计划", "",
                      "来源：昨日「明日待办」+ 今日新增计划", ""])
        plan_rows = [(time_label, summary, remark or "-")
                     for time_label, summary, remark in today_plan]
        lines.append(build_table(plan_rows, ["时间", "事项", "备注"]))
        lines.append("")

    # ✅ 今日完成
    if today_done:
        lines.extend(["## ✅ 今日完成", ""])
        done_rows = [(summary, "-", "-") for _, summary, _ in today_done]
        lines.append(build_table(done_rows, ["完成", "未完成", "调整"]))
        lines.append("")

    # ⏰ 明日待办
    if tomorrow_todo:
        lines.extend(["## ⏰ 明日待办", ""])
        todo_rows = [(time_label, summary, remark or "-")
                     for time_label, summary, remark in tomorrow_todo]
        lines.append(build_table(todo_rows, ["时间", "事项", "备注"]))
        lines.append("")

    # 📌 待跟进
    if followup:
        lines.extend(["## 📌 待跟进", "", "🔴 紧急  🟡 一般  🟢 缓办", ""])
        for time_label, summary, remark in followup:
            lines.append(f"- {summary}")
        lines.append("")

    return "\n".join(lines)


# ─── 主流程 ─────────────────────────────────────────────

def main():
    date_str = get_cst_now().strftime("%Y-%m-%d")
    print(f"正在生成 {date_str} 的复盘...", file=sys.stderr)

    folder_token = ensure_folder_structure()
    if not folder_token:
        print("无法获取文件夹，退出", file=sys.stderr)
        sys.exit(1)

    doc_id = find_doc_in_folder(folder_token, date_str)

    # 拉取数据
    print("拉取飞书任务...", file=sys.stderr)
    tasks_data = get_today_tasks()
    today_plan, today_done, tomorrow_todo, followup = tasks_data
    print(f"  今日到期: {len(today_plan)}, 今日完成: {len(today_done)}, 明日到期: {len(tomorrow_todo)}, 待跟进: {len(followup)}", file=sys.stderr)

    print("拉取飞书日历...", file=sys.stderr)
    calendar_events = get_today_calendar()
    print(f"  日历事件: {len(calendar_events)}", file=sys.stderr)

    markdown = build_markdown(date_str, tasks_data, calendar_events)

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

    # stdout 推微信（简版），stderr 写日志
    plan_count = len(today_plan)
    done_count = len(today_done)
    todo_count = len(tomorrow_todo)
    cal_count = len(calendar_events)

    lines_out = [f"✅ {date_str} 复盘", ""]

    # 今日计划
    lines_out.append("📋 今日计划")
    if today_plan:
        for _, summary, _ in today_plan:
            lines_out.append(f"  ✗ {summary}")
    else:
        lines_out.append("  （暂无）")
    lines_out.append("")

    # 今日完成
    lines_out.append("✅ 今日完成")
    if today_done:
        for _, summary, _ in today_done:
            lines_out.append(f"  ✓ {summary}")
    else:
        lines_out.append("  （暂无）")
    lines_out.append("")

    # 明日待办
    lines_out.append("⏰ 明日待办")
    if tomorrow_todo:
        for _, summary, _ in tomorrow_todo:
            lines_out.append(f"  → {summary}")
    else:
        lines_out.append("  （暂无）")
    lines_out.append("")

    # 今日日程
    if calendar_events:
        lines_out.append("📅 今日日程")
        for t, name in calendar_events:
            lines_out.append(f"  {t} {name}")
        lines_out.append("")

    lines_out.append(f"📄 [{FEISHU_FOLDER}{date_str}-复盘总结](https://feishu.cn/docx/{doc_id})")

    print("\n".join(lines_out))


if __name__ == "__main__":
    main()
