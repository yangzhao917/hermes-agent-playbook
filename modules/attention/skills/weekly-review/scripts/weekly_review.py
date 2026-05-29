#!/usr/bin/env python3
"""
weekly-review: 本周事实 + 下周取舍

Facts come from daily-review documents under AgentOS/10-复盘/每日复盘.
The weekly output is a Feishu doc under AgentOS/10-复盘/每周复盘.
"""

import argparse
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta, timezone

os.environ.setdefault("HERMES_HOME", "/home/ubuntu/.hermes")

SH_TZ = timezone(timedelta(hours=8))
FEISHU_ROOT_FOLDER_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"
DAILY_REVIEW_FOLDER_TOKEN = "A36SfM8iOlqrBHdg4SScF0atn8g"
WEEKLY_REVIEW_PATH = ["AgentOS", "10-复盘", "每周复盘"]
SCRIPT_WARNINGS = []

MAINLINE_NAMES = [
    "Hermes / AgentOS 系统建设",
    "AI Agent 求职",
    "小红书个人品牌",
    "健康、睡眠、财务和生活质量",
    "十堰黑客松社区轻运营",
]

MODE_LABELS = {
    "committed": "今天真正要推进的",
    "maintain": "先别掉线的",
    "incubate": "先攒着的",
    "waiting": "等反馈的",
    "delegated": "已经交给别人处理的",
    "archived": "已结束的",
}

MAINLINE_META = {name: {"id": name, "name": name, "mode": "committed", "user_label": "今天真正要推进的", "aliases": []} for name in MAINLINE_NAMES}


def load_dynamic_mainlines():
    """Load non-archived AgentOS attention mainlines from Hermes runtime state."""
    try:
        import yaml
        state_path = Path.home() / ".hermes/state/agentos/mainlines.yaml"
        data = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        rows = [
            item for item in data.get("mainlines", [])
            if item.get("name") and item.get("mode") != "archived"
        ]
        rows.sort(key=lambda item: (int(item.get("priority") or 999), item.get("name")))
        for item in rows:
            item["user_label"] = item.get("user_label") or MODE_LABELS.get(item.get("mode"), item.get("mode"))
        names = [item["name"] for item in rows]
        meta = {item["name"]: item for item in rows}
        if names:
            return names, meta
    except Exception as exc:
        SCRIPT_WARNINGS.append(f"动态主线读取失败，使用内置快照：{str(exc)[:120]}")
    return MAINLINE_NAMES, MAINLINE_META


MAINLINE_NAMES, MAINLINE_META = load_dynamic_mainlines()


KNOWLEDGE_KEYWORDS = [
    "规则", "SOP", "流程", "方案", "架构", "路径", "迁移", "统一",
    "修复", "排查", "踩坑", "配置", "部署", "token", "gateway", "cron",
    "lark-cli", "Kanban", "飞书", "ima", "Hermes", "AgentOS",
]


def run_lark(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        SCRIPT_WARNINGS.append(f"命令超时：{' '.join(cmd[:3])}")
        return None
    if result.returncode != 0:
        SCRIPT_WARNINGS.append(result.stdout.strip()[:240] or f"命令失败：{' '.join(cmd[:3])}")
        return None
    return result.stdout


def parse_json_output(text):
    if not text:
        return None
    idx = text.find("{")
    if idx < 0:
        return None
    try:
        return json.loads(text[idx:])
    except json.JSONDecodeError:
        return None


def get_cst_now():
    return datetime.now(SH_TZ)


def week_range(week_start_arg=None):
    if week_start_arg:
        start = datetime.fromisoformat(week_start_arg).astimezone(SH_TZ)
    else:
        now = get_cst_now()
        start = now - timedelta(days=now.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6)
    return start, end


def date_range(start_arg, end_arg):
    start = datetime.fromisoformat(start_arg).astimezone(SH_TZ)
    end = datetime.fromisoformat(end_arg).astimezone(SH_TZ)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end.replace(hour=0, minute=0, second=0, microsecond=0)
    if end < start:
        raise ValueError("--end-date 不能早于 --start-date")
    return start, end


def format_weekly_title(start, end):
    iso_year, iso_week, _ = start.isocalendar()
    return (
        f"{iso_year}-W{iso_week:02d}"
        f"({start.strftime('%m.%d')}-{end.strftime('%m.%d')})"
        "-每周复盘"
    )

def list_folder(folder_token):
    out = run_lark([
        "lark-cli", "drive", "files", "list",
        "--params", json.dumps({"folder_token": folder_token, "page_size": 50}, ensure_ascii=False),
        "--format", "json",
    ])
    data = parse_json_output(out)
    if not data:
        return []
    return data.get("data", {}).get("files", [])


def get_folder_token(folder_name, parent_token):
    for item in list_folder(parent_token):
        if item.get("name") == folder_name and item.get("type") == "folder":
            return item.get("token")
    out = run_lark([
        "lark-cli", "drive", "files", "create_folder",
        "--data", json.dumps({"name": folder_name, "folder_token": parent_token}, ensure_ascii=False),
        "--format", "json",
    ])
    data = parse_json_output(out)
    if not data:
        return None
    payload = data.get("data", {})
    return payload.get("token") or payload.get("file", {}).get("token")


def ensure_weekly_folder():
    parent = FEISHU_ROOT_FOLDER_TOKEN
    for folder_name in WEEKLY_REVIEW_PATH:
        parent = get_folder_token(folder_name, parent)
        if not parent:
            return None
    return parent


def find_doc(title, folder_token):
    for item in list_folder(folder_token):
        if item.get("name") == title and item.get("type") in ("docx", "doc"):
            return item.get("token")
    return None


def create_doc(title, folder_token):
    out = run_lark([
        "lark-cli", "docs", "+create",
        "--title", title,
        "--folder-token", folder_token,
        "--markdown", " ",
    ])
    data = parse_json_output(out)
    if not data:
        return None
    return data.get("data", {}).get("doc_id")


def update_doc(doc_id, markdown):
    out = run_lark([
        "lark-cli", "docs", "+update",
        "--doc", doc_id,
        "--markdown", markdown,
        "--mode", "overwrite",
    ], timeout=45)
    return out is not None


def fetch_doc_markdown(doc_token):
    out = run_lark(["lark-cli", "docs", "+fetch", "--doc", doc_token, "--format", "json"])
    data = parse_json_output(out)
    if not data:
        return ""
    return data.get("data", {}).get("markdown", "")


def daily_docs_for_week(start, end):
    wanted = {(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)}
    docs = []
    for item in list_folder(DAILY_REVIEW_FOLDER_TOKEN):
        name = item.get("name", "")
        m = re.match(r"^(\d{4}-\d{2}-\d{2})-每日复盘$", name)
        if not m or m.group(1) not in wanted:
            continue
        docs.append({
            "date": m.group(1),
            "title": name,
            "token": item.get("token"),
            "url": item.get("url"),
        })
    docs.sort(key=lambda x: x["date"])
    return docs


def extract_section(markdown, heading):
    pattern = rf"^##\s+.*{re.escape(heading)}.*$"
    lines = markdown.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if re.match(pattern, line):
            start = idx + 1
            break
    if start is None:
        return []
    out = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped and stripped != "（暂无）":
            out.append(stripped)
    return out


def bullets(lines):
    result = []
    for line in lines:
        if line.startswith("- "):
            result.append(line[2:].strip())
    return result


def cap(items, n):
    seen = set()
    result = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", item).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
        if len(result) >= n:
            break
    return result


def summarize_docs(docs):
    completed = []
    followups = []
    content = []
    knowledge = []
    mainlines = defaultdict(list)
    source_links = []

    for doc in docs:
        md = fetch_doc_markdown(doc["token"])
        source_links.append(f"- [{doc['title']}]({doc.get('url') or 'https://feishu.cn/docx/' + doc['token']})")
        completed.extend([f"{doc['date']}：{x}" for x in bullets(extract_section(md, "今日完成"))])
        followups.extend([f"{doc['date']}：{x}" for x in bullets(extract_section(md, "后续跟进"))])
        followups.extend([f"{doc['date']}：{x}" for x in bullets(extract_section(md, "明日待办"))])
        content.extend([f"{doc['date']}：{x}" for x in bullets(extract_section(md, "内容素材"))])

        for b in bullets(extract_section(md, "输入与长期记忆")):
            if any(k.lower() in b.lower() for k in KNOWLEDGE_KEYWORDS):
                knowledge.append(f"{doc['date']}：{b}")

        ml_lines = extract_section(md, "主线证据候选") or extract_section(md, "五条主线推进")
        current = None
        for line in ml_lines:
            if line.startswith("### "):
                current = line[4:].strip()
                continue
            if current and line.startswith("- "):
                mainlines[current].append(f"{doc['date']}：{line[2:].strip()}")
                if any(k.lower() in line.lower() for k in KNOWLEDGE_KEYWORDS):
                    knowledge.append(f"{doc['date']}：{line[2:].strip()}")

        for b in bullets(extract_section(md, "今日收获")):
            knowledge.append(f"{doc['date']}：{b}")

    return {
        "completed": cap(completed, 20),
        "followups": cap(followups, 15),
        "content": cap(content, 12),
        "knowledge": cap(knowledge, 12),
        "mainlines": {k: cap(v, 6) for k, v in mainlines.items()},
        "source_links": source_links,
    }



def mainline_entries(summary, name):
    meta = MAINLINE_META.get(name, {})
    entries = list(summary["mainlines"].get(name, []))
    for alias in meta.get("aliases") or []:
        entries.extend(summary["mainlines"].get(alias, []))
    return cap(entries, 6)


def mainline_review_suggestions(summary):
    suggestions = []
    committed_count = sum(1 for item in MAINLINE_META.values() if item.get("mode") == "committed")
    for name in MAINLINE_NAMES:
        meta = MAINLINE_META.get(name, {})
        mode = meta.get("mode", "maintain")
        entries = mainline_entries(summary, name)
        count = len(entries)
        recommendation = "保持当前处理方式"
        target = mode
        reason = "当前处理方式与本周证据基本匹配。"
        if mode == "committed" and count == 0:
            recommendation = "需要确认是否继续作为下周重点"
            target = "incubate"
            reason = "本周没有明显行动证据，继续占用重点可能稀释注意力。"
        elif mode in ("incubate", "maintain") and count >= 2 and committed_count < 3:
            recommendation = "可确认是否放入下周重点"
            target = "committed"
            reason = "本周出现多条证据，但是否进入重点需要你确认。"
        elif mode == "delegated" and count > 0:
            recommendation = "只做升级检查"
            reason = "已交给别人处理的事项出现证据，不默认收回责任。"
        command = None
        if target != mode:
            line_id = meta.get("id", name)
            command = (
                "python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py "
                f"update-mode {line_id} {target} --reason {json.dumps(reason, ensure_ascii=False)}"
            )
        suggestions.append({
            "name": name,
            "mode": mode,
            "user_label": meta.get("user_label") or MODE_LABELS.get(mode, mode),
            "evidence_count": count,
            "recommendation": recommendation,
            "target_mode": target,
            "reason": reason,
            "command": command,
        })
    return suggestions


def build_doc(title, start, end, docs, summary):
    lines = []
    suggestions = mainline_review_suggestions(summary)
    lines.append("## 本周结论")
    lines.append(f"- 周期：{start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}")
    lines.append(f"- 数据来源：{len(docs)} 份每日复盘")
    moved = [s for s in suggestions if s["mode"] == "committed" and s["evidence_count"] > 0]
    if moved:
        lines.append("- 本周真正推进了：" + "、".join(s["name"] for s in moved[:3]))
    else:
        lines.append("- 本周没有看到明确的重点推进证据。")
    lines.append("")

    lines.append("## 下周建议")
    keep = [s for s in suggestions if s["target_mode"] == "committed" or (s["mode"] == "committed" and s["recommendation"] == "保持当前处理方式")]
    for idx, item in enumerate(keep[:3], 1):
        lines.append(f"{idx}. {item['name']}：{item['reason']}")
    if not keep:
        lines.append("- 先从 AgentOS / 求职 中选 1-2 件真正推进。")
    lines.append("")

    lines.append("## 本周真正推进了什么")
    for name in MAINLINE_NAMES:
        entries = mainline_entries(summary, name)
        if entries:
            lines.append(f"### {name}（{(MAINLINE_META.get(name) or {}).get('user_label', '')}）")
            lines.extend(f"- {x}" for x in entries)
    if not summary["mainlines"]:
        lines.append("（暂无明显主线证据）")
    lines.append("")

    lines.append("## 本周完成明细")
    lines.extend(f"- {x}" for x in summary["completed"]) if summary["completed"] else lines.append("（暂无明确完成记录）")
    lines.append("")

    lines.append("## 没推进/需要确认的事")
    needs = [s for s in suggestions if s["recommendation"] != "保持当前处理方式"]
    for item in needs:
        lines.append(f"- {item['name']}：{item['recommendation']}。{item['reason']}")
        if item.get("command"):
            lines.append(f"  - 确认后执行：`{item['command']}`")
    if not needs:
        lines.append("（暂无）")
    lines.append("")

    lines.append("## 主线阶段进展")
    for name in MAINLINE_NAMES:
        meta = MAINLINE_META.get(name, {})
        stage = meta.get("current_stage") or {}
        if stage:
            lines.append(f"- {name}：{stage.get('name', '未定义阶段')}；检查点：{stage.get('review_at', '未设置')}")
    lines.append("")

    lines.append("## 内容素材")
    lines.extend(f"- {x}" for x in summary["content"]) if summary["content"] else lines.append("（暂无）")
    lines.append("")
    lines.append("## 需要跟进")
    lines.extend(f"- {x}" for x in summary["followups"]) if summary["followups"] else lines.append("（暂无）")
    lines.append("")
    lines.append("## 数据质量和不确定部分")
    lines.append("- 周复盘只基于每日复盘文档和已读取事实；不编造健康、睡眠、财务、微信聊天数据。")
    if not docs:
        lines.append("- 本周缺少每日复盘数据，先恢复数据闭环。")
    if SCRIPT_WARNINGS:
        lines.extend(f"- {w}" for w in cap(SCRIPT_WARNINGS, 8))
    lines.append("")
    lines.append("## 来源")
    lines.extend(summary["source_links"] or ["（暂无）"])
    return "\n".join(lines)


def build_wechat_msg(title, doc_url, start, end, summary):
    suggestions = mainline_review_suggestions(summary)
    moved = [s for s in suggestions if s["mode"] == "committed" and s["evidence_count"] > 0]
    keep = [s for s in suggestions if s["target_mode"] == "committed" or (s["mode"] == "committed" and s["recommendation"] == "保持当前处理方式")]
    quiet = [s for s in suggestions if s["mode"] in ("incubate", "maintain", "delegated")]
    needs = [s for s in suggestions if s["recommendation"] != "保持当前处理方式"]
    lines = [f"📌 {title}", f"{start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}", ""]
    lines.append("本周真正推进了：")
    lines.extend(f"- {x['name']}：{x['evidence_count']} 条证据" for x in moved[:3] or [])
    if not moved:
        lines.append("- 没有看到明确重点推进证据")
    lines.append("")
    lines.append("下周建议只抓：")
    lines.extend(f"{i}. {x['name']}" for i, x in enumerate(keep[:3], 1)) if keep else lines.append("1. 从 AgentOS / 求职 中选 1-2 件")
    lines.append("")
    lines.append("先不用花力气：")
    lines.extend(f"- {x['name']}：{x['user_label']}" for x in quiet[:5] or ["暂无"])
    lines.append("")
    lines.append("需要确认：")
    lines.extend(f"- {x['name']}：{x['recommendation']}" for x in needs[:3]) if needs else lines.append("- 暂无")
    lines.append("")
    if doc_url:
        lines.append(f"📄 完整复盘已写入飞书：[AgentOS/10-复盘/每周复盘/{title}]({doc_url})")
    else:
        lines.append("📄 文档同步失败，请查看数据质量说明")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week-start", type=str, help="周一日期 YYYY-MM-DD，默认本周周一")
    parser.add_argument("--start-date", type=str, help="自定义复盘开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="自定义复盘结束日期 YYYY-MM-DD")
    parser.add_argument("--check-path", action="store_true", help="只检查每周复盘目录")
    args, _ = parser.parse_known_args()

    folder_tok = ensure_weekly_folder()
    if args.check_path:
        print("/".join(WEEKLY_REVIEW_PATH))
        print(folder_tok or "")
        return

    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            raise SystemExit("--start-date 和 --end-date 必须同时提供")
        start, end = date_range(args.start_date, args.end_date)
    else:
        start, end = week_range(args.week_start)
    docs = daily_docs_for_week(start, end)
    summary = summarize_docs(docs)
    title = format_weekly_title(start, end)

    doc_url = ""
    if folder_tok:
        doc_id = find_doc(title, folder_tok)
        if not doc_id:
            doc_id = create_doc(title, folder_tok)
        if doc_id:
            markdown = build_doc(title, start, end, docs, summary)
            if update_doc(doc_id, markdown):
                doc_url = f"https://feishu.cn/docx/{doc_id}"
    else:
        SCRIPT_WARNINGS.append("无法定位 AgentOS/10-复盘/每周复盘 文件夹")

    print(build_wechat_msg(title, doc_url, start, end, summary))


if __name__ == "__main__":
    main()
