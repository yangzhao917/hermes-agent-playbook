#!/usr/bin/env python3
"""
Memory cleanup script — runs via terminal tool in cron environment.
Reads ~/.hermes/memories/MEMORY.md, applies cleanup rules, writes back.

Usage:
    python3 ~/.hermes/scripts/memory_cleanup.py

Output:
    - Console: human-readable cleanup report
    - Log: appends to ~/.hermes/logs/memory_cleanup.log

Cleanup rules (in priority order):
    1. [过期版本号] 含版本号如 "CLI 1.0.15" 的记录
    2. [失效临时教训] 一次性事件记录超过1周且无长期价值的
    3. [完全重复] 完全相同内容出现多次的条目
    4. [skill冗余] skill/playbook 已有完整记录的内容（通过关键词重叠判断）
"""
import os
import re
import argparse
import shutil
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path.home() / ".hermes" / "memories" / "MEMORY.md"
SKILLS_DIR = Path.home() / ".hermes" / "skills"
AGENT_OS_DIR = Path.home() / ".hermes" / "agent-os"
LEGACY_PLAYBOOK_DIR = Path.home() / ".hermes" / "hermes-agent-playbook"
ENTRY_DELIMITER = "\n§\n"


def read_entries(path: Path) -> list:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return []
    entries = [e.strip() for e in raw.split(ENTRY_DELIMITER)]
    return [e for e in entries if e]


def write_entries(path: Path, entries: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ENTRY_DELIMITER.join(entries) if entries else ""
    path.write_text(content, encoding="utf-8")


def get_playbook_content():
    texts = []
    repo_dir = AGENT_OS_DIR if AGENT_OS_DIR.exists() else LEGACY_PLAYBOOK_DIR
    if repo_dir.exists():
        for md in repo_dir.rglob("*.md"):
            try:
                texts.append(md.read_text(encoding="utf-8").lower())
            except Exception:
                pass
    return " ".join(texts)


def get_skills_content():
    texts = []
    if SKILLS_DIR.exists():
        for md in SKILLS_DIR.rglob("*.md"):
            try:
                texts.append(md.read_text(encoding="utf-8").lower())
            except Exception:
                pass
    return " ".join(texts)


def is_version_pattern(s: str) -> bool:
    return bool(re.search(r"(?:v|version|\b)\d+\.\d+\.\d+", s))


def is_old_date(s: str) -> bool:
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{4}/\d{2}/\d{2}",
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}",
    ]
    for p in date_patterns:
        if re.search(p, s, re.IGNORECASE):
            return True
    return False


def keyword_overlaps_skill(entry: str, skills_text: str) -> bool:
    words = [w.strip().lower() for w in re.findall(r'\b\w{4,}\b', entry)]
    significant = [w for w in words if w not in {
        "the", "and", "for", "with", "from", "this", "that", "have", "been",
        "需要", "使用", "这个", "那个", "是的", "不是", "用户", "一个"
    }]
    count = sum(1 for w in significant if w in skills_text)
    return count >= 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="preview cleanup without writing MEMORY.md")
    args = parser.parse_args()

    playbook_text = get_playbook_content()
    skills_text = get_skills_content()
    entries = read_entries(MEMORY_FILE)

    if not entries:
        print("🧹 记忆清理报告\n\n无记忆条目，无需清理。")
        return

    to_delete = []
    to_keep = []

    for entry in entries:
        reasons = []

        if is_version_pattern(entry):
            reasons.append("含过期版本号")

        if is_old_date(entry) and "一次性" in entry:
            reasons.append("一次性临时教训（超过1周）")

        if entries.count(entry) > 1:
            reasons.append("完全重复条目")

        if keyword_overlaps_skill(entry, skills_text):
            reasons.append("skill/playbook 已有记录")

        if reasons:
            to_delete.append((entry, "; ".join(reasons)))
        else:
            to_keep.append(entry)

    # Console output
    print("🧹 记忆清理报告\n")
    if to_delete:
        action_label = "将删除" if args.dry_run else "删除了"
        print(f"{action_label}（{len(to_delete)} 条）：")
        for entry, reason in to_delete:
            preview = entry[:60] + ("..." if len(entry) > 60 else "")
            print(f"  • {preview} — {reason}")
        print()
    else:
        print("无需要删除的条目。\n")

    print(f"保留了（{len(to_keep)} 条）：")
    for entry in to_keep:
        preview = entry[:60] + ("..." if len(entry) > 60 else "")
        print(f"  • {preview}")

    # Write back
    if not args.dry_run:
        if MEMORY_FILE.exists():
            backup = MEMORY_FILE.with_suffix(f".{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak")
            shutil.copy2(MEMORY_FILE, backup)
        write_entries(MEMORY_FILE, to_keep)

    # Append log
    log_path = Path.home() / ".hermes" / "logs" / "memory_cleanup.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = "dry-run" if args.dry_run else "write"
    log_lines = [f"[{timestamp}] === 记忆清理报告 ({mode}) ==="]
    if to_delete:
        for entry, reason in to_delete:
            preview = entry[:80] + ("..." if len(entry) > 80 else "")
            log_lines.append(f"  {'将删除' if args.dry_run else '删除'}: {preview} | {reason}")
    else:
        log_lines.append("  无需要删除的条目")
    for entry in to_keep:
        preview = entry[:80] + ("..." if len(entry) > 80 else "")
        log_lines.append(f"  保留: {preview}")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")


if __name__ == "__main__":
    main()
