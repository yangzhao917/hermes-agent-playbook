#!/usr/bin/env python3
"""
daily-review v3: 每日注意力收口
- 微信版: 注意力收口和确认入口
- 飞书文档: 事实档案和可追溯复盘记录
"""

import subprocess
from concurrent.futures import ThreadPoolExecutor
import os
import re
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

os.environ.setdefault("HERMES_HOME", "/home/ubuntu/.hermes")

SH_TZ = timezone(timedelta(hours=8))
CAL_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py"
TASK_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-task/scripts/list_tasks.py"
DRIVE_LIST = "/home/ubuntu/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py"  # placeholder
SCRIPT_TIMEOUT_SECONDS = 25
SCRIPT_WARNINGS = []


def check_feishu_token():
    """检查飞书 token 是否有效，返回 (is_valid, reason)"""
    try:
        result = subprocess.run(
            ["lark-cli", "auth", "status"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        if "tokenStatus" in output and '"valid"' in output:
            return True, "ok"
        if "expiresAt" in output:
            return False, "token 已过期"
        return False, f"auth status 异常: {output[:120]}"
    except Exception as e:
        return False, f"检查失败: {e}"


def try_refresh_feishu_token():
    """尝试通过轻量 API 调用触发 lark-cli 自动刷新 token"""
    try:
        subprocess.run(
            ["lark-cli", "task", "tasks", "list",
             "--params", '{"page_size":1}'],
            capture_output=True, text=True, timeout=15
        )
        # 无论返回什么，只要触发了请求就可能刷新了 token
        return check_feishu_token()
    except Exception as e:
        return False, f"刷新失败: {e}"
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


def get_review_date(date_arg=None):
    """确定复盘日期：优先参数，其次今天"""
    if date_arg:
        return datetime.fromisoformat(date_arg).astimezone(SH_TZ)
    return get_cst_now()


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
        m = re.match(r"^✓\s+(.+?)\s+截止\s+(\d{2}/\d{2})(?:\s+周\S+)?$", line)
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
        m = re.match(r"^○\s+(.+?)\s+截止\s+(\d{2}/\d{2})(?:\s+周\S+)?$", line)
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
        m = re.match(r"^○\s+(.+?)\s+截止\s+(\d{2}/\d{2})(?:\s+周\S+)?$", line)
        if m and m.group(2) == tomorrow:
            results.append(m.group(1).strip())
    return results


def infer_mainline(text):
    lower = text.lower()
    for name, keywords in MAINLINES:
        for kw in keywords:
            if kw.lower() in lower:
                return name
    return None


def summarize_mainline_progress(done, today_todo, tomorrow_todo, calendar_ev):
    progress = {name: {"done": [], "open": []} for name, _ in MAINLINES}
    for item in done:
        line = infer_mainline(item)
        if line:
            progress[line]["done"].append(item)
    for item in today_todo + tomorrow_todo:
        line = infer_mainline(item)
        if line:
            progress[line]["open"].append(item)
    for _, item in calendar_ev:
        line = infer_mainline(item)
        if line:
            progress[line]["done"].append(f"参与/安排：{item}")
    return progress


def extract_content_materials(done, calendar_ev):
    keywords = ["小红书", "内容", "活动", "黑客松", "Agent", "Hermes", "求职", "面试", "微信读书", "读书"]
    items = []
    for item in done:
        if any(k.lower() in item.lower() for k in keywords):
            items.append(item)
    for _, item in calendar_ev:
        if any(k.lower() in item.lower() for k in keywords):
            items.append(item)
    return items[:5]


def detect_busywork(done, today_todo, tomorrow_todo, calendar_ev):
    texts = done + today_todo + tomorrow_todo + [s for _, s in calendar_ev]
    if not texts:
        return "今天记录较少，先保证明天有 1 个可展示产出。"
    core_hits = 0
    for text in texts:
        line = infer_mainline(text)
        if line in ("AI Agent 求职", "Hermes 系统建设"):
            core_hits += 1
    if done and core_hits == 0:
        return "今天有完成事项，但没有明显推进求职或 Hermes，注意不要用外围事务填满一天。"
    if not done and (today_todo or calendar_ev):
        return "今天有安排但完成记录为空，明天要收敛到 1-3 个能交付的任务。"
    return "未发现明显伪忙碌；继续用可展示产出检验投入。"


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

FEISHU_ROOT_FOLDER_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"
REVIEW_DOC_PATH = ["AgentOS", "10-复盘", "每日复盘"]
EXPECTED_REVIEW_FOLDER_TOKEN = "A36SfM8iOlqrBHdg4SScF0atn8g"
FORBIDDEN_REVIEW_FOLDER_NAMES = {"HermesAgent"}


def find_doc(title, folder_token):
    """在文件夹中查找同名文档，返回 doc_id 或 None"""
    title_aliases = {title}
    if title.endswith("-每日复盘"):
        title_aliases.add(title.replace("-每日复盘", "-复盘总结"))
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
        if f.get("name") in title_aliases and f.get("type") in ("docx", "doc"):
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
        data = d.get("data", {})
        return data.get("token") or data.get("file", {}).get("token")
    return None


def ensure_review_folder():
    """确保 AgentOS/10-复盘/每日复盘 文件夹存在，返回 folder_token"""
    parent = FEISHU_ROOT_FOLDER_TOKEN
    for folder_name in REVIEW_DOC_PATH:
        if folder_name in FORBIDDEN_REVIEW_FOLDER_NAMES:
            raise RuntimeError(f"禁止写入旧复盘目录：{folder_name}")
        parent = get_folder_token(folder_name, parent)
        if not parent:
            return None
    return parent


def check_review_folder_path():
    folder_tok = ensure_review_folder()
    path = "/".join(REVIEW_DOC_PATH)
    if folder_tok != EXPECTED_REVIEW_FOLDER_TOKEN:
        raise RuntimeError(
            f"复盘目录 token 异常：path={path}, got={folder_tok}, "
            f"expected={EXPECTED_REVIEW_FOLDER_TOKEN}"
        )
    return path, folder_tok


# ── Markdown 构建 ─────────────────────────────────────────

def build_table(rows, cols):
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for row in rows:
        cells = [str(c) if c else "-" for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)



def mode_label(name):
    return (MAINLINE_META.get(name) or {}).get("user_label", "")


def attention_sections(done, today_todo, tomorrow_todo, calendar_ev):
    progress = summarize_mainline_progress(done, today_todo, tomorrow_todo, calendar_ev)
    moved = []
    quiet = []
    confirmations = []
    uncertainties = []
    for name, _ in MAINLINES:
        meta = MAINLINE_META.get(name) or {}
        mode = meta.get("mode")
        done_items = progress[name]["done"]
        open_items = progress[name]["open"]
        if mode == "committed":
            if done_items:
                moved.append(f"{name}：{done_items[0]}")
            else:
                confirmations.append(f"{name} 今天没有看到行动证据，明天是否仍保留为重点？")
        elif mode == "incubate":
            quiet.append(f"{name}：先攒素材，不强制推进")
        elif mode == "maintain":
            quiet.append(f"{name}：只看异常或明确任务")
        elif mode == "waiting":
            quiet.append(f"{name}：等反馈或检查点")
        elif mode == "delegated":
            delegated_to = meta.get("delegated_to") or "别人"
            quiet.append(f"{name}：{delegated_to}负责，只有升级条件才提醒")
    if not done and not calendar_ev:
        uncertainties.append("今天完成和日程事实较少，不做强判断。")
    uncertainties.append("没有健康、睡眠、财务数据，所以不判断恢复状态或消费状态。")
    return {
        "moved": moved,
        "tomorrow_focus": tomorrow_todo[:2],
        "quiet": quiet,
        "confirmations": confirmations,
        "uncertainties": uncertainties,
        "progress": progress,
    }

def build_feishu_doc(date_str, done, today_todo, tomorrow_todo, calendar_ev, review_date, harvest=None, weread_facts=None, ima_facts=None):
    """构建飞书文档完整 Markdown：事实档案 + 注意力收口。"""
    lines = []
    attention = attention_sections(done, today_todo, tomorrow_todo, calendar_ev)
    content_materials = extract_content_materials(done, calendar_ev)
    busywork = detect_busywork(done, today_todo, tomorrow_todo, calendar_ev)

    lines.append("## 🧭 注意力收口")
    lines.append("### 今天真正推进了什么")
    lines.extend(f"- {x}" for x in attention["moved"] or ["（没有看到明确行动证据）"])
    lines.append("")
    lines.append("### 明天建议抓什么")
    lines.extend(f"- {x}" for x in attention["tomorrow_focus"] or ["（暂无明确明日待办；建议从今天真正要推进的主线里选一个最小动作）"])
    lines.append("")
    lines.append("### 先不用花力气的事")
    lines.extend(f"- {x}" for x in attention["quiet"] or ["（暂无）"])
    lines.append("")
    lines.append("### 需要确认/纠偏")
    lines.extend(f"- {x}" for x in attention["confirmations"] or ["（暂无）"])
    lines.append("")
    lines.append("### 我不确定的部分")
    lines.extend(f"- {x}" for x in attention["uncertainties"])
    lines.append("")

    lines.append("## 📍 完整事实：今日日历")
    lines.extend(f"- {t} {s}" for t, s in calendar_ev) if calendar_ev else lines.append("（暂无）")
    lines.append("")
    lines.append("## ✅ 完整事实：今日完成")
    lines.extend(f"- {s}" for s in done) if done else lines.append("（暂无）")
    lines.append("")
    lines.append("## ⏰ 明日待办")
    lines.extend(f"- {s}" for s in tomorrow_todo) if tomorrow_todo else lines.append("（暂无）")
    lines.append("")
    lines.append("## 🔜 后续跟进")
    lines.extend(f"- {s}" for s in today_todo) if today_todo else lines.append("（暂无）")
    lines.append("")

    lines.append("## 🧭 主线证据候选")
    any_progress = False
    for name, _ in MAINLINES:
        done_items = attention["progress"][name]["done"]
        open_items = attention["progress"][name]["open"]
        if not done_items and not open_items:
            continue
        any_progress = True
        lines.append(f"### {name}（{mode_label(name)}）")
        lines.extend(f"- 行动事实候选：{item}" for item in done_items[:3])
        lines.extend(f"- 待处理事实候选：{item}" for item in open_items[:3])
    if not any_progress:
        lines.append("（暂无明显主线证据候选）")
    lines.append("")

    lines.append("## 📚 输入与长期记忆候选")
    input_facts = list(weread_facts or []) + list(ima_facts or [])
    lines.extend(f"- {item}" for item in input_facts[:5]) if input_facts else lines.append("（暂无可用事实）")
    lines.append("")
    lines.append("## 🧩 内容素材")
    lines.extend(f"- {item}" for item in content_materials) if content_materials else lines.append("（暂无，可从微信读书划线、活动见闻、求职/AgentOS 进展中提炼）")
    lines.append("")
    lines.append("## 💡 今日收获")
    lines.append(harvest or "（暂无）")
    lines.append("")
    lines.append("## 🧯 忙碌质量检查")
    lines.append(f"- {busywork}")
    lines.append("")
    lines.append("## ⚠️ 数据质量说明")
    if SCRIPT_WARNINGS:
        lines.extend(f"- {warning}" for warning in SCRIPT_WARNINGS[:5])
    lines.append("- 未接入健康、睡眠、财务、微信聊天数据；相关判断不做强结论。")
    lines.append("- 关键词命中只算候选证据，不等于真实推进。")
    return "\n".join(lines)


def build_wechat_msg(date_str, done, today_todo, tomorrow_todo, doc_title, doc_url, review_date, calendar_ev, weread_facts=None, ima_facts=None):
    """构建微信推送文本：注意力收口优先。"""
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    day_name = day_names[review_date.weekday()]
    attention = attention_sections(done, today_todo, tomorrow_todo, calendar_ev)
    lines = [f"📌 {date_str} {day_name} 复盘", ""]
    lines.append("今天真正推进了：")
    lines.extend(f"- {x}" for x in attention["moved"] or ["（没有看到明确行动证据）"])
    lines.append("")
    lines.append("明天建议只抓：")
    lines.extend(f"{i}. {x}" for i, x in enumerate(attention["tomorrow_focus"][:2], 1)) if attention["tomorrow_focus"] else lines.append("1. 从 AgentOS / 求职 中选一个最小动作")
    lines.append("")
    lines.append("先不用花力气：")
    lines.extend(f"- {x}" for x in attention["quiet"][:5] or ["（暂无）"])
    lines.append("")
    lines.append("需要你确认：")
    lines.extend(f"- {x}" for x in attention["confirmations"][:3] or ["（暂无）"])
    lines.append("")
    lines.append("我不确定的部分：")
    lines.extend(f"- {x}" for x in attention["uncertainties"][:3])
    lines.append("")
    if doc_url:
        lines.append(f"📄 完整事实档案：[AgentOS/10-复盘/每日复盘/{doc_title}]({doc_url})")
    else:
        lines.append("📄 飞书文档同步失败，请查看数据质量说明")
    return "\n".join(lines)


# ── 主流程 ───────────────────────────────────────────────

def main():
    import argparse as _argparse
    _parser = _argparse.ArgumentParser()
    _parser.add_argument("--date", type=str, help="复盘日期 YYYY-MM-DD（默认昨天）")
    _parser.add_argument("--check-path", action="store_true", help="只检查复盘写入目录，不生成文档")
    _args, _ = _parser.parse_known_args()

    if _args.check_path:
        try:
            path, token = check_review_folder_path()
            print(f"{path}\n{token}")
        except Exception as e:
            print(f"check-path failed: {e}")
        return

    review_date = get_review_date(_args.date)
    date_str = review_date.strftime("%Y-%m-%d")
    tomorrow_date = (review_date + timedelta(days=1)).strftime("%m/%d")
    today_mmdd = review_date.strftime("%m/%d")

    # 1. 拉数据
    with ThreadPoolExecutor(max_workers=6) as executor:
        fut_done = executor.submit(fetch_today_done, today_mmdd)
        fut_today_todo = executor.submit(fetch_today_todo, today_mmdd)
        fut_tomorrow_todo = executor.submit(fetch_tomorrow_todo, tomorrow_date)
        fut_calendar = executor.submit(fetch_today_calendar, date_str)
        fut_weread = executor.submit(fetch_weread_monthly_summary)
        fut_ima = executor.submit(fetch_ima_recent_summary)
        done = fut_done.result()
        today_todo = fut_today_todo.result()
        tomorrow_todo = fut_tomorrow_todo.result()
        calendar_ev = fut_calendar.result()
        weread_facts = fut_weread.result()
        ima_facts = fut_ima.result()

    # 2. 飞书文档（幂等：同日覆盖）
    token_ok, token_reason = check_feishu_token()
    if not token_ok:
        SCRIPT_WARNINGS.append(f"token 首次检查失败：{token_reason}，尝试刷新...")
        token_ok, token_reason = try_refresh_feishu_token()
        if token_ok:
            SCRIPT_WARNINGS.append("token 刷新成功，继续同步文档")
        else:
            SCRIPT_WARNINGS.append(f"token 刷新失败，文档同步已跳过：{token_reason}")

    folder_tok = None
    if token_ok:
        try:
            _, folder_tok = check_review_folder_path()
        except Exception as e:
            SCRIPT_WARNINGS.append(f"复盘目录检查失败，文档同步已跳过：{e}")
    doc_title = f"{date_str}-每日复盘"
    doc_url = ""

    if not token_ok:
        pass  # 已在上面记录警告
    elif folder_tok:
        doc_id = find_doc(doc_title, folder_tok)
        if not doc_id:
            doc_id = create_doc(doc_title, folder_tok)
        if doc_id:
            markdown = build_feishu_doc(date_str, done, today_todo,
                                        tomorrow_todo, calendar_ev, review_date,
                                        weread_facts=weread_facts, ima_facts=ima_facts)
            update_doc(doc_id, markdown)
            doc_url = f"https://feishu.cn/docx/{doc_id}"

    # 3. 微信推送（stdout）
    wechat = build_wechat_msg(date_str, done, today_todo, tomorrow_todo,
                              doc_title, doc_url, review_date, calendar_ev,
                              weread_facts=weread_facts, ima_facts=ima_facts)
    print(wechat)


if __name__ == "__main__":
    main()
