#!/usr/bin/env python3
"""
morning-reminder: 每日晨间日程提醒
- 今日日程（时间线）
- 今日待办（截止≤今天，含逾期预警）
- 明日日程（前3条+总数）
- 三角色行动建议（主线、核心任务、自动化）
"""

import subprocess
from concurrent.futures import ThreadPoolExecutor
import json
import re
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

SH_TZ = timezone(timedelta(hours=8))
CAL_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py"
TASK_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-task/scripts/list_tasks.py"
SCRIPT_TIMEOUT_SECONDS = 25
SCRIPT_WARNINGS = []
WEREAD_KEY_FILE = Path("/home/ubuntu/.config/weread/api_key")
IMA_SKILL_DIR = Path("/home/ubuntu/.hermes/skills/ima-skill")

MAINLINES = [
    ("Hermes / AgentOS 系统建设", ["Hermes", "AgentOS", "Agent", "技能", "skill", "飞书", "ima", "微信读书", "自动化", "数据", "系统", "PRD", "复盘", "主线"]),
    ("AI Agent 求职", ["求职", "简历", "面试", "岗位", "投递", "招聘", "AI Agent", "agent 岗", "offer", "作品集"]),
    ("小红书个人品牌", ["小红书", "xhs", "内容", "笔记", "选题", "账号", "发布", "传播", "视频", "个人品牌"]),
    ("健康、睡眠、财务和生活质量", ["健康", "睡眠", "运动", "体检", "消费", "收入", "支出", "财务", "生活", "恢复"]),
    ("十堰黑客松社区轻运营", ["十堰", "黑客松", "社区", "活动", "国正", "合作", "宣发"]),
]

MODE_LABELS = {
    "committed": "今天真正要推进的",
    "maintain": "先别掉线的",
    "incubate": "先攒着的",
    "waiting": "等反馈的",
    "delegated": "已经交给别人处理的",
    "archived": "已结束的",
}

MAINLINE_META = {name: {"mode": "committed", "user_label": "今天真正要推进的"} for name, _ in MAINLINES}


def load_dynamic_mainlines():
    """Load AgentOS attention mainlines from Hermes runtime state."""
    try:
        import yaml
        state_path = Path.home() / ".hermes/state/agentos/mainlines.yaml"
        data = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        loaded = []
        meta = {}
        for item in data.get("mainlines", []):
            mode = item.get("mode", "maintain")
            if mode == "archived":
                continue
            item["user_label"] = item.get("user_label") or MODE_LABELS.get(mode, mode)
            name = item.get("name")
            keywords = item.get("keywords") or []
            if name and keywords:
                loaded.append((name, keywords))
                meta[name] = item
        if loaded:
            return loaded, meta
    except Exception as exc:
        try:
            SCRIPT_WARNINGS.append(f"动态主线读取失败，使用内置快照：{str(exc)[:120]}")
        except Exception:
            pass
    return MAINLINES, MAINLINE_META


MAINLINES, MAINLINE_META = load_dynamic_mainlines()


def get_cst_now():
    return datetime.now(SH_TZ)


def run_script(path, *args):
    cmd = ["python3", path] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        SCRIPT_WARNINGS.append(f"{path} 超时，已按空数据降级")
        return ""
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip().splitlines()
        detail = err[-1] if err else f"exit={result.returncode}"
        SCRIPT_WARNINGS.append(f"{path} 执行失败：{detail[:120]}")
    return result.stdout.strip()


def seconds_to_hm(seconds):
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        seconds = 0
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    if hours:
        return f"{hours}小时{minutes}分钟"
    return f"{minutes}分钟"


def fetch_weread_monthly_summary():
    """Read-only WeRead monthly stats. Returns short fact lines."""
    if not WEREAD_KEY_FILE.exists():
        return []
    key = WEREAD_KEY_FILE.read_text().strip()
    if not key:
        return []
    payload = json.dumps({
        "api_name": "/readdata/detail",
        "mode": "monthly",
        "skill_version": "1.0.3",
    }, ensure_ascii=False)
    try:
        req = urllib.request.Request(
            "https://i.weread.qq.com/api/agent/gateway",
            data=payload.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=SCRIPT_TIMEOUT_SECONDS) as resp:
            response_text = resp.read().decode("utf-8", errors="replace")
    except Exception:
        SCRIPT_WARNINGS.append("微信读书读取失败或超时，已跳过")
        return []
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        SCRIPT_WARNINGS.append("微信读书返回非 JSON，已跳过")
        return []
    if data.get("errcode"):
        SCRIPT_WARNINGS.append(f"微信读书返回错误：{data.get('errmsg') or data.get('msg')}")
        return []
    lines = []
    if data.get("totalReadTime") is not None:
        lines.append(f"本月阅读 {seconds_to_hm(data.get('totalReadTime'))}")
    if data.get("readDays") is not None:
        lines.append(f"阅读天数 {data.get('readDays')} 天")
    longest = data.get("readLongest") or []
    if longest:
        item = longest[0]
        book = item.get("book") or item.get("albumInfo") or {}
        title = book.get("title") or book.get("name")
        if title:
            lines.append(f"本月读得最多：《{title}》")
    return lines[:3]


def fetch_ima_recent_summary():
    """Read-only ima recent note list. Returns short fact lines."""
    api = IMA_SKILL_DIR / "ima_api.cjs"
    if not api.exists():
        return []
    payload = '{"folder_id":"","sort_type":0,"cursor":"","limit":3}'
    try:
        result = subprocess.run(
            ["node", str(api), "openapi/note/v1/list_note", payload],
            cwd=str(IMA_SKILL_DIR),
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        SCRIPT_WARNINGS.append("ima 最近笔记读取超时，已跳过")
        return []
    if result.returncode != 0:
        SCRIPT_WARNINGS.append("ima 最近笔记读取失败，已跳过")
        return []
    try:
        obj = json.loads(result.stdout)
    except json.JSONDecodeError:
        SCRIPT_WARNINGS.append("ima 返回非 JSON，已跳过")
        return []
    if obj.get("code") not in (0, None):
        SCRIPT_WARNINGS.append(f"ima 返回错误：{obj.get('msg')}")
        return []
    notes = ((obj.get("data") or {}).get("note_book_list") or [])[:3]
    titles = [n.get("title") for n in notes if n.get("title")]
    if not titles:
        return []
    return [f"ima 最近笔记：{'; '.join(titles[:3])}"]


# ── 日历 ────────────────────────────────────────────────

def fetch_events_today():
    """今日所有日程，返回 [(time_str, summary), ...]"""
    out = run_script(CAL_LIST, "--today")
    return _parse_events_output(out)


def fetch_events_tomorrow():
    """明日所有日程，返回 [(time_str, summary), ...]"""
    out = run_script(CAL_LIST, "--tomorrow")
    return _parse_events_output(out)


def _parse_events_output(raw: str) -> list:
    """从 list_events.py 输出中提取 HH:MM 标题行"""
    lines = raw.split("\n")
    events = []
    for line in lines[1:]:  # 跳过标题行
        line = line.strip()
        if not line or "暂无" in line:
            continue
        # 格式: "  05/22 16:20 ~ 05/22 19:23  标题"
        m = re.match(r"^\d{2}/\d{2}\s+(\d{2}:\d{2})\s+~\s+\d{2}/\d{2}\s+\d{2}:\d{2}\s+(.+)$", line)
        if m:
            events.append((m.group(1), m.group(2)))
            continue
    return events


# ── 任务 ────────────────────────────────────────────────

def fetch_todos():
    """获取所有未完成任务，返回 [(summary, due_str, overdue_days), ...]"""
    out = run_script(TASK_LIST, "--status", "todo")
    tasks = []
    lines = out.split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("📋") or "暂无" in line:
            continue
        # 匹配 "  ○ 标题[emoji]  截止 MM/DD 周X" 或 "  ○ 标题  截止 无期限"
        m = re.match(r"^○\s+(\S(?:\S|\s)*?)\s+截止\s+(\d{2}/\d{2}(?:\s+周\S+)?|无期限)$", line)
        if m:
            title = m.group(1).strip()
            due_str = m.group(2)
            overdue_days = None
            if due_str != "无期限":
                # due_str 可能是 "MM/DD" 或 "MM/DD 周X"
                due_mmdd = due_str.split(" ")[0]
                due_month, due_day = int(due_mmdd[:2]), int(due_mmdd[3:])
                today = get_cst_now().date()
                due_this_year = datetime(today.year, due_month, due_day).date()
                due_next_year = datetime(today.year + 1, due_month, due_day).date()
                candidates = [due_this_year, due_next_year]
                overdue_candidates = [d for d in candidates if d < today]
                if overdue_candidates:
                    overdue_days = (today - min(overdue_candidates, key=lambda d: today - d)).days
            tasks.append((title, due_str, overdue_days))
    return tasks


# ── 格式化 ──────────────────────────────────────────────

def format_header():
    now = get_cst_now()
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    day_name = day_names[now.weekday()]
    date_str = now.strftime("%Y-%m-%d")
    print(f"📌 {date_str} {day_name}")
    print()


def format_today_events(events):
    print("☀️ 今日日程")
    if not events:
        print("  （暂无安排 🎉）")
        return
    for t, title in events:
        print(f"  {t} {title}")


def classify_tasks(tasks):
    """将任务分为逾期+今天截止 vs 未来截止"""
    today = get_cst_now().date()
    urgent, future = [], []
    for title, due_str, overdue_days in tasks:
        if overdue_days is not None:
            urgent.append((title, due_str, overdue_days))
        elif due_str == "无期限":
            future.append((title, due_str, None))
        else:
            # 今天截止（已排除逾期，上面算过了）
            # due_str 可能是 "MM/DD" 或 "MM/DD 周X"
            due_mmdd = due_str.split(" ")[0]
            due_month, due_day = int(due_mmdd[:2]), int(due_mmdd[3:])
            due_this_year = datetime(today.year, due_month, due_day).date()
            due_next_year = datetime(today.year + 1, due_month, due_day).date()
            candidates = [d for d in [due_this_year, due_next_year] if d >= today]
            due_date = min(candidates) if candidates else due_this_year
            if due_date == today:
                urgent.append((title, due_str, None))
            else:
                future.append((title, due_str, None))
    urgent.sort(key=lambda x: x[1])
    future.sort(key=lambda x: x[1] or "")
    return urgent, future


def format_today_todos(tasks):
    print()
    print("📋 逾期/今日截止")
    urgent, future = classify_tasks(tasks)

    if not urgent and not future:
        print("  （全部完成 🎉）")
        return

    if not urgent:
        print("  （今日无截止 🎉）")

    for title, due_str, overdue_days in urgent:
        if overdue_days is not None:
            print(f"  ⚠️ {title}  逾期{overdue_days}天")
        else:
            print(f"  ○ {title}  截止 {due_str}")


def format_future_todos(tasks):
    print()
    print("📋 后续待办")
    _, future = classify_tasks(tasks)
    if not future:
        print("  （暂无）")
        return
    for title, due_str, _ in future:
        print(f"  ○ {title}  截止 {due_str}")


def format_tomorrow_events(events):
    print()
    total = len(events)
    label = f"📅 明日日程（{total}项）"
    if total == 0:
        print(label)
        print("  （暂无预告 🎉）")
        return
    shown = events[:3]
    print(label)
    for t, title in shown:
        print(f"  {t} {title}")


def format_input_memory_facts(weread_facts, ima_facts):
    print()
    print("📚 输入/记忆事实")
    facts = []
    facts.extend(weread_facts)
    facts.extend(ima_facts)
    if not facts:
        print("  （暂无可用事实）")
        return
    for item in facts[:5]:
        print(f"  - {item}")


def infer_mainline(text):
    lower = text.lower()
    for name, keywords in MAINLINES:
        for kw in keywords:
            if kw.lower() in lower:
                return name
    return None


def score_mainlines(today_ev, tasks):
    scores = {name: 0 for name, _ in MAINLINES}

    def should_score(line):
        status = (MAINLINE_META.get(line) or {}).get("status", "later")
        return (MAINLINE_META.get(line) or {}).get("mode") == "committed"

    for _, title in today_ev:
        line = infer_mainline(title)
        if line and should_score(line):
            scores[line] += 2
    urgent, future = classify_tasks(tasks)
    for title, _, overdue_days in urgent:
        line = infer_mainline(title)
        if line and should_score(line):
            scores[line] += 4 if overdue_days is not None else 3
    for title, _, _ in future:
        line = infer_mainline(title)
        if line and should_score(line):
            scores[line] += 1
    return scores


def choose_focus_line(today_ev, tasks):
    scores = score_mainlines(today_ev, tasks)
    best = max(scores.items(), key=lambda item: item[1])
    if best[1] > 0:
        return best[0], scores
    return None, scores


def select_core_tasks(today_ev, tasks):
    urgent, future = classify_tasks(tasks)
    selected = []
    for title, due_str, overdue_days in urgent:
        suffix = f"逾期{overdue_days}天" if overdue_days is not None else f"截止 {due_str}"
        selected.append(f"{title}（{suffix}）")
    for t, title in today_ev:
        selected.append(f"{t} {title}")
    for title, due_str, _ in future:
        selected.append(f"{title}（后续，{due_str}）")
    return selected[:3]


def format_role_advice(today_ev, tasks, tomorrow_ev):
    focus_line, scores = choose_focus_line(today_ev, tasks)
    urgent, future = classify_tasks(tasks)
    core_tasks = select_core_tasks(today_ev, tasks)
    committed = [name for name, meta in MAINLINE_META.items() if meta.get("mode") == "committed"]

    print()
    print("🧭 今天建议只抓")
    if len(committed) > 3:
        print("  本周真正要推进的事超过 3 条，建议先收敛，否则会互相挤占注意力。")
    if core_tasks:
        for idx, item in enumerate(core_tasks[:2], 1):
            print(f"  {idx}. {item}")
            print("     为什么：来自今日/逾期待办或日程事实。")
            print("     确定性：依据一般")
    elif focus_line:
        print(f"  1. {focus_line}")
        print("     为什么：这是当前真正要推进的主线，但今天缺少明确任务。")
        print("     确定性：依据一般，需要你确认下一步。")
    else:
        print("  （今天缺少明确事实；先不要强行安排，建议手动指定一个最小动作。）")

    print()
    print("🌿 先不用花太多力气")
    quiet = []
    for name, meta in MAINLINE_META.items():
        mode = meta.get("mode")
        if mode == "incubate":
            quiet.append(f"{name}：先攒素材，不强制推进")
        elif mode == "maintain":
            quiet.append(f"{name}：只看异常或明确任务")
        elif mode == "waiting":
            quiet.append(f"{name}：等反馈或检查点")
        elif mode == "delegated":
            delegated_to = meta.get("delegated_to") or "别人"
            quiet.append(f"{name}：{delegated_to}负责，只有升级条件才提醒")
    for item in quiet[:5] or ["暂无"]:
        print(f"  - {item}")

    fact_bits = []
    if today_ev:
        fact_bits.append(f"今日日程 {len(today_ev)} 项")
    if urgent:
        fact_bits.append(f"逾期/今日截止 {len(urgent)} 项")
    if future:
        fact_bits.append(f"后续待办 {len(future)} 项")
    if tomorrow_ev:
        fact_bits.append(f"明日预告 {len(tomorrow_ev)} 项")
    print()
    print("📎 我看到的事实：" + ("；".join(fact_bits) if fact_bits else "今天事实较少。"))
    if SCRIPT_WARNINGS:
        print("⚠️ 我不确定的部分：")
        for warning in SCRIPT_WARNINGS[:3]:
            print(f"  - {warning}")
    print("🧯 防幻读：关键词命中只算候选，不等于真实推进；缺健康/睡眠/财务数据时不做强判断。")


def main():
    format_header()
    with ThreadPoolExecutor(max_workers=5) as executor:
        fut_today_ev = executor.submit(fetch_events_today)
        fut_tomorrow_ev = executor.submit(fetch_events_tomorrow)
        fut_todos = executor.submit(fetch_todos)
        fut_weread = executor.submit(fetch_weread_monthly_summary)
        fut_ima = executor.submit(fetch_ima_recent_summary)
        today_ev = fut_today_ev.result()
        tomorrow_ev = fut_tomorrow_ev.result()
        todos = fut_todos.result()
        weread_facts = fut_weread.result()
        ima_facts = fut_ima.result()

    format_today_events(today_ev)
    format_today_todos(todos)
    format_future_todos(todos)
    format_tomorrow_events(tomorrow_ev)
    format_input_memory_facts(weread_facts, ima_facts)
    format_role_advice(today_ev, todos, tomorrow_ev)


if __name__ == "__main__":
    main()
