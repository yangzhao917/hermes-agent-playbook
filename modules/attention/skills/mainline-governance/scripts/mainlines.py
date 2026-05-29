#!/usr/bin/env python3
"""Manage AgentOS attention mainlines for Hermes."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml


SH_TZ = timezone(timedelta(hours=8))
DEFAULT_STATE = Path.home() / ".hermes/state/agentos/mainlines.yaml"
AUDIT_LOG = Path.home() / ".hermes/logs/agentos/mainline_events.jsonl"
VALID_MODES = {"committed", "maintain", "incubate", "waiting", "delegated", "archived"}
MODE_LABELS = {
    "committed": "今天真正要推进的",
    "maintain": "先别掉线的",
    "incubate": "先攒着的",
    "waiting": "等反馈的",
    "delegated": "已经交给别人处理的",
    "archived": "已结束的",
}
LEGACY_STATUS_MODE = {
    "now": "committed",
    "next": "incubate",
    "later": "maintain",
    "paused": "delegated",
    "archived": "archived",
}


def now_iso() -> str:
    return datetime.now(SH_TZ).isoformat(timespec="seconds")


def envelope(**kwargs) -> dict:
    result = {
        "ok": True,
        "facts": [],
        "inferences": [],
        "uncertainties": [],
        "recommendations": [],
        "requires_confirmation": False,
    }
    result.update(kwargs)
    return result


def load_state(path: Path = DEFAULT_STATE) -> dict:
    if not path.exists():
        raise SystemExit(f"mainline state file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("version", 2)
    data.setdefault("mainlines", [])
    return normalize_state(data)


def normalize_state(data: dict) -> dict:
    for line in data.get("mainlines", []):
        if not line.get("mode"):
            line["mode"] = LEGACY_STATUS_MODE.get(line.get("status", "later"), "maintain")
        line["user_label"] = line.get("user_label") or MODE_LABELS.get(line["mode"], line["mode"])
    return data


def save_state(data: dict, path: Path = DEFAULT_STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(path.suffix + f".bak-{datetime.now(SH_TZ).strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(path, backup)
    data["version"] = 2
    data["updated_at"] = now_iso()
    for line in data.get("mainlines", []):
        line.pop("status", None)
        line["user_label"] = MODE_LABELS.get(line.get("mode"), line.get("user_label", ""))
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def audit(action: str, payload: dict) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": now_iso(), "action": action, **payload}
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def normalize(text: str) -> str:
    return (text or "").lower()


def find_line(data: dict, line_id: str) -> dict:
    for line in data.get("mainlines", []):
        if line.get("id") == line_id:
            return line
    raise SystemExit(f"mainline not found: {line_id}")


def active_lines(data: dict, include_archived: bool = False) -> list[dict]:
    lines = data.get("mainlines", [])
    if include_archived:
        return lines
    return [x for x in lines if x.get("mode") != "archived"]


def validate_mode(mode: str) -> str:
    if mode not in VALID_MODES:
        raise SystemExit(f"invalid mode {mode}; valid: {', '.join(sorted(VALID_MODES))}")
    return mode


def mode_should_surface(mode: str, text: str = "", line: dict | None = None) -> tuple[bool, str, str]:
    if mode == "committed":
        return True, "依据充分", "这是当前真正要推进的主线。"
    if mode == "delegated":
        policy = "；".join((line or {}).get("escalation_policy") or [])
        hit = any(str(x) and str(x) in text for x in (line or {}).get("escalation_policy") or [])
        if hit:
            return True, "依据一般", "命中委托事项的升级条件，需要检查是否介入。"
        return False, "依据一般", f"这件事已交给别人处理，只在升级条件出现时提醒。升级条件：{policy or '未配置'}"
    if mode == "maintain":
        return False, "依据不足", "这是保持不掉线的事项；没有异常或明确任务时不主动制造行动。"
    if mode == "incubate":
        return False, "依据一般", "这更适合先攒素材和机会，不默认进入本周重点。"
    if mode == "waiting":
        return False, "依据一般", "这是等反馈/等时间的事项，到期、超时或有外部反馈时再提醒。"
    return False, "依据充分", "已结束的事项不主动提醒。"


def command_list(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    lines = active_lines(data, include_archived=args.include_archived)
    if args.mode:
        lines = [x for x in lines if x.get("mode") == args.mode]
    lines = sorted(lines, key=lambda x: (int(x.get("priority") or 999), x.get("name") or ""))
    committed = [x for x in lines if x.get("mode") == "committed"]
    recs = []
    if len(committed) > 3:
        recs.append({
            "type": "focus_reduction",
            "text": "今天真正要推进的主线超过 3 条，建议先收敛，否则会互相挤占注意力。",
            "confidence": "依据充分",
        })
    print(json.dumps(envelope(
        facts=[f"读取到 {len(lines)} 条非归档主线。"],
        mainlines=lines,
        recommendations=recs,
        needs_focus_reduction=len(committed) > 3,
    ), ensure_ascii=False, indent=2))


def classify_text(data: dict, text: str) -> dict:
    haystack = normalize(text)
    candidates = []
    for line in active_lines(data):
        score = 0
        matched = []
        for kw in line.get("keywords") or []:
            needle = normalize(str(kw))
            if needle and needle in haystack:
                score += 1
                matched.append(str(kw))
        if score:
            mode = line.get("mode", "maintain")
            mode_weight = {"committed": 3, "incubate": 2, "maintain": 1, "waiting": 1, "delegated": 0}.get(mode, 0)
            should_surface, confidence, reason = mode_should_surface(mode, text, line)
            candidates.append({
                "id": line.get("id"),
                "name": line.get("name"),
                "mode": mode,
                "user_label": line.get("user_label") or MODE_LABELS.get(mode, mode),
                "score": score,
                "rank_score": score * 10 + mode_weight - int(line.get("priority") or 99) / 100,
                "matched_keywords": matched,
                "should_surface": should_surface,
                "confidence": confidence,
                "reason": reason,
                "delegated_to": line.get("delegated_to"),
                "escalation_policy": line.get("escalation_policy", []),
            })
    candidates.sort(key=lambda x: x["rank_score"], reverse=True)
    best = candidates[0] if candidates else None
    facts = []
    inferences = []
    uncertainties = []
    if best:
        facts.append(f"文本命中关键词：{', '.join(best['matched_keywords'])}")
        inferences.append(f"候选主线为「{best['name']}」，当前处理方式是「{best['user_label']}」。")
        if best["confidence"] != "依据充分":
            uncertainties.append("关键词命中只能作为候选证据，不等于真实推进。")
    else:
        uncertainties.append("没有命中明确主线；不要强行归类。")
    return envelope(
        text=text,
        mainline=best,
        confidence=best["confidence"] if best else "依据不足",
        candidates=candidates[:5],
        facts=facts,
        inferences=inferences,
        uncertainties=uncertainties,
        requires_confirmation=False,
    )


def command_classify(args: argparse.Namespace) -> None:
    print(json.dumps(classify_text(load_state(args.state), args.text), ensure_ascii=False, indent=2))


def command_update_mode(args: argparse.Namespace) -> None:
    mode = validate_mode(args.mode)
    data = load_state(args.state)
    line = find_line(data, args.id)
    old = line.get("mode")
    line["mode"] = mode
    line["user_label"] = MODE_LABELS[mode]
    if args.reason:
        line["last_mode_reason"] = args.reason
    save_state(data, args.state)
    audit("update-mode", {
        "target": args.id,
        "from": old,
        "to": mode,
        "reason": args.reason,
        "confirmed_by": args.confirmed_by,
        "result": "success",
    })
    print(json.dumps(envelope(
        facts=[f"{line.get('name')} 从 {old} 调整为 {mode}。"],
        id=args.id,
        old_mode=old,
        new_mode=mode,
        user_label=MODE_LABELS[mode],
    ), ensure_ascii=False, indent=2))


def command_update_status(args: argparse.Namespace) -> None:
    legacy = args.status
    mode = LEGACY_STATUS_MODE[legacy]
    args.mode = mode
    command_update_mode(args)


def command_update_stage(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    line = find_line(data, args.id)
    old = line.get("current_stage") or {}
    stage = dict(old)
    if args.name:
        stage["name"] = args.name
    if args.review_at:
        stage["review_at"] = args.review_at
    if args.done_when:
        stage["done_when"] = args.done_when
    if args.acceptance_evidence:
        stage["acceptance_evidence"] = args.acceptance_evidence
    line["current_stage"] = stage
    save_state(data, args.state)
    audit("update-stage", {"target": args.id, "old": old, "new": stage, "reason": args.reason, "result": "success"})
    print(json.dumps(envelope(facts=[f"{line.get('name')} 当前阶段已更新。"], current_stage=stage), ensure_ascii=False, indent=2))


def command_create(args: argparse.Namespace) -> None:
    mode = validate_mode(args.mode)
    data = load_state(args.state)
    if any(x.get("id") == args.id for x in data.get("mainlines", [])):
        raise SystemExit(f"mainline already exists: {args.id}")
    line = {
        "id": args.id,
        "name": args.name,
        "mode": mode,
        "user_label": MODE_LABELS[mode],
        "priority": args.priority,
        "objective": args.objective or "",
        "owner": args.owner,
        "keywords": args.keyword or [],
        "current_stage": {
            "name": args.stage_name or "试运行一周",
            "review_at": args.review_at or "",
            "done_when": args.done_when or [],
            "acceptance_evidence": args.acceptance_evidence or [],
        },
    }
    data.setdefault("mainlines", []).append(line)
    save_state(data, args.state)
    audit("create", {"id": args.id, "name": args.name, "mode": mode, "reason": args.reason})
    print(json.dumps(envelope(facts=[f"已创建主线：{args.name}。"], mainline=line), ensure_ascii=False, indent=2))


def command_archive(args: argparse.Namespace) -> None:
    args.mode = "archived"
    command_update_mode(args)


def command_delete(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    lines = data.get("mainlines", [])
    target = find_line(data, args.id)
    if not args.yes:
        raise SystemExit("delete requires --yes; prefer archive unless this was a mistaken or duplicate entry")
    data["mainlines"] = [x for x in lines if x.get("id") != args.id]
    save_state(data, args.state)
    audit("delete", {"id": args.id, "name": target.get("name"), "reason": args.reason, "result": "success"})
    print(json.dumps(envelope(facts=[f"已删除误建/重复主线：{target.get('name')}。"], deleted=args.id), ensure_ascii=False, indent=2))


def command_merge(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    source = find_line(data, args.source_id)
    target = find_line(data, args.target_id)
    source["mode"] = "archived"
    source["user_label"] = MODE_LABELS["archived"]
    source["merged_into"] = target.get("id")
    source["last_mode_reason"] = args.reason
    save_state(data, args.state)
    audit("merge", {"source_id": args.source_id, "target_id": args.target_id, "reason": args.reason, "result": "success"})
    print(json.dumps(envelope(facts=[f"已合并 {source.get('name')} 到 {target.get('name')}。"]), ensure_ascii=False, indent=2))


def parse_evidence_counts(raw_items: list[str] | None, raw_json: str | None) -> dict[str, int]:
    counts: dict[str, int] = {}
    if raw_json:
        payload = json.loads(raw_json)
        for key, value in payload.items():
            counts[str(key)] = int(value)
    for item in raw_items or []:
        if "=" not in item:
            raise SystemExit("--evidence-count must be in id=count form")
        key, value = item.split("=", 1)
        counts[key] = int(value)
    return counts


def command_suggest_review(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    counts = parse_evidence_counts(args.evidence_count, args.evidence_json)
    suggestions = []
    committed_count = sum(1 for x in active_lines(data) if x.get("mode") == "committed")

    for line in sorted(active_lines(data), key=lambda x: (int(x.get("priority") or 999), x.get("name") or "")):
        line_id = line.get("id")
        name = line.get("name")
        mode = line.get("mode", "maintain")
        evidence_count = counts.get(line_id, counts.get(name, 0))
        recommendation = "保持当前处理方式"
        target_mode = mode
        reason = "当前处理方式与本周期证据基本匹配。"
        requires_confirmation = False

        if mode == "committed" and evidence_count == 0:
            recommendation = "需要确认是否继续作为下周重点"
            target_mode = "incubate"
            reason = "本周期没有明显行动证据，继续占用重点可能稀释注意力。"
            requires_confirmation = True
        elif mode in ("incubate", "maintain") and evidence_count >= 2 and committed_count < 3:
            recommendation = "可确认是否放入下周重点"
            target_mode = "committed"
            reason = "本周期出现多条证据，但是否进入重点需要用户确认。"
            requires_confirmation = True
        elif mode == "delegated" and evidence_count > 0:
            recommendation = "只做升级检查"
            reason = "已交给别人处理的事项出现证据，不默认收回责任。"

        command = None
        if target_mode != mode:
            command = (
                "python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py "
                f"update-mode {line_id} {target_mode} --reason {json.dumps(reason, ensure_ascii=False)}"
            )
        suggestions.append({
            "id": line_id,
            "name": name,
            "mode": mode,
            "user_label": line.get("user_label"),
            "evidence_count": evidence_count,
            "recommendation": recommendation,
            "target_mode": target_mode,
            "reason": reason,
            "command": command,
            "requires_confirmation": requires_confirmation,
        })

    print(json.dumps(envelope(recommendations=suggestions), ensure_ascii=False, indent=2))


def command_correction(args: argparse.Namespace) -> None:
    text = args.text.strip()
    lower = text.lower()
    data = load_state(args.state)
    requires_confirmation = False
    action = "correction-note"
    recommendation = "已记录为纠偏线索。"
    target = None
    new_value = None

    if "不是" in text and "是" in text:
        action = "classification-correction"
        recommendation = "这是归类纠偏，低影响；可用于修正当前复盘或建议，不自动写长期偏好。"
    elif "这周" in text and ("别管" in text or "先别" in text):
        action = "temporary-mute"
        recommendation = "这是本周临时降噪，不写成长期偏好。"
    elif "以后" in text or "长期" in text:
        action = "preference-candidate"
        recommendation = "这是长期偏好候选，需要确认后才能写入规则。"
        requires_confirmation = True
    elif "交给" in text or "委托" in text:
        action = "delegate-candidate"
        recommendation = "这是委托调整候选，需要确认后才能改主线处理方式。"
        requires_confirmation = True
        new_value = "delegated"
    elif "结束" in text or "归档" in text:
        action = "archive-candidate"
        recommendation = "这是归档候选，需要确认后才能归档。"
        requires_confirmation = True
        new_value = "archived"
    elif "撤销" in text:
        action = "undo-request"
        recommendation = "这是撤销请求；请执行 undo-last 查看并回滚最近一次主线变更。"
        requires_confirmation = True

    audit("correction", {
        "source": "wechat",
        "user_text": text,
        "target": target,
        "new_value": new_value,
        "scope": "current_review" if not requires_confirmation else "candidate",
        "requires_confirmation": requires_confirmation,
        "result": "recorded",
    })
    print(json.dumps(envelope(
        facts=[f"收到纠偏：{text}"],
        inferences=[recommendation],
        action=action,
        requires_confirmation=requires_confirmation,
        recommendations=[{"text": recommendation, "requires_confirmation": requires_confirmation}],
    ), ensure_ascii=False, indent=2))


def command_undo_last(args: argparse.Namespace) -> None:
    if not AUDIT_LOG.exists():
        print(json.dumps(envelope(uncertainties=["还没有可撤销的主线变更。"], requires_confirmation=False), ensure_ascii=False, indent=2))
        return
    entries = [json.loads(x) for x in AUDIT_LOG.read_text(encoding="utf-8").splitlines() if x.strip()]
    reversible = [x for x in entries if x.get("action") == "update-mode" and x.get("from") and x.get("to")]
    if not reversible:
        print(json.dumps(envelope(uncertainties=["没有找到可撤销的 update-mode 记录。"], requires_confirmation=False), ensure_ascii=False, indent=2))
        return
    last = reversible[-1]
    data = load_state(args.state)
    line = find_line(data, last["target"])
    current = line.get("mode")
    line["mode"] = last["from"]
    line["user_label"] = MODE_LABELS[last["from"]]
    save_state(data, args.state)
    audit("undo-last", {"target": last["target"], "from": current, "to": last["from"], "reverted_event": last, "result": "success"})
    print(json.dumps(envelope(facts=[f"已撤销最近一次主线调整：{last['target']} 从 {current} 恢复为 {last['from']}。"]), ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage AgentOS attention mainlines")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list")
    p.add_argument("--mode", choices=sorted(VALID_MODES))
    p.add_argument("--include-archived", action="store_true")
    p.set_defaults(func=command_list)

    p = sub.add_parser("classify")
    p.add_argument("text")
    p.set_defaults(func=command_classify)

    p = sub.add_parser("update-mode")
    p.add_argument("id")
    p.add_argument("mode", choices=sorted(VALID_MODES))
    p.add_argument("--reason", default="")
    p.add_argument("--confirmed-by", default="manual")
    p.set_defaults(func=command_update_mode)

    p = sub.add_parser("update-status")
    p.add_argument("id")
    p.add_argument("status", choices=sorted(LEGACY_STATUS_MODE))
    p.add_argument("--reason", default="")
    p.add_argument("--confirmed-by", default="legacy-alias")
    p.set_defaults(func=command_update_status)

    p = sub.add_parser("update-stage")
    p.add_argument("id")
    p.add_argument("--name")
    p.add_argument("--review-at")
    p.add_argument("--done-when", action="append")
    p.add_argument("--acceptance-evidence", action="append")
    p.add_argument("--reason", default="")
    p.set_defaults(func=command_update_stage)

    p = sub.add_parser("create")
    p.add_argument("id")
    p.add_argument("name")
    p.add_argument("--mode", default="incubate", choices=sorted(VALID_MODES))
    p.add_argument("--priority", type=int, default=99)
    p.add_argument("--objective", default="")
    p.add_argument("--owner", default="yang")
    p.add_argument("--keyword", action="append")
    p.add_argument("--stage-name")
    p.add_argument("--review-at")
    p.add_argument("--done-when", action="append")
    p.add_argument("--acceptance-evidence", action="append")
    p.add_argument("--reason", default="")
    p.set_defaults(func=command_create)

    p = sub.add_parser("archive")
    p.add_argument("id")
    p.add_argument("--reason", default="")
    p.add_argument("--confirmed-by", default="manual")
    p.set_defaults(func=command_archive)

    p = sub.add_parser("delete")
    p.add_argument("id")
    p.add_argument("--reason", default="")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=command_delete)

    p = sub.add_parser("merge")
    p.add_argument("source_id")
    p.add_argument("target_id")
    p.add_argument("--reason", default="")
    p.set_defaults(func=command_merge)

    p = sub.add_parser("suggest-review")
    p.add_argument("--evidence-count", action="append")
    p.add_argument("--evidence-json")
    p.set_defaults(func=command_suggest_review)

    p = sub.add_parser("correction")
    p.add_argument("--text", required=True)
    p.set_defaults(func=command_correction)

    p = sub.add_parser("undo-last")
    p.set_defaults(func=command_undo_last)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
