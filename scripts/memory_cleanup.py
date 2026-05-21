#!/usr/bin/env python3
"""
记忆自动清理脚本
- 支持 --dry-run 预览模式
- 排除 USER.md
- 结构化 JSON 日志
- 无记忆时跳过，写心跳
"""
import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

MEMORY_DIR = Path.home() / ".hermes" / "memories"
MEMORY_FILE = MEMORY_DIR / "MEMORY.md"
LOG_FILE = Path.home() / ".hermes" / "logs" / "memory_cleanup.jsonl"
ENTRY_DELIMITER = "\n§\n"
ONE_WEEK_AGO = datetime.now(timezone.utc) - timedelta(days=7)


def read_entries(path: Path) -> list:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return []
    entries = [e.strip() for e in raw.split(ENTRY_DELIMITER)]
    return [e for e in entries if e]


def is_version_pattern(s: str) -> bool:
    """匹配版本号如 v1.2.3、CLI 1.0.15。"""
    return bool(re.search(r"(?:v|version|\b)\d+\.\d+(?:\.\d+)?", s, re.IGNORECASE))


def is_older_than_one_week(s: str) -> bool:
    """匹配日期并判断是否超过一周。"""
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{4}/\d{2}/\d{2}",
    ]
    for p in date_patterns:
        m = re.search(p, s)
        if m:
            try:
                date_str = m.group().replace("/", "-")
                entry_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                return entry_date < ONE_WEEK_AGO
            except ValueError:
                pass
    return False


def find_exact_duplicates(entries: list) -> dict:
    """返回 {entry: [index_positions]}，只返回重复（>1个）的。"""
    positions = {}
    for i, e in enumerate(entries):
        positions.setdefault(e, []).append(i)
    return {e: pos for e, pos in positions.items() if len(pos) > 1}


def classify_entry(entry: str) -> tuple:
    """
    判断单条是否应删除，返回 (should_delete, reason)。
    reason 为 None 表示应保留。
    """
    # 规则1: 含版本号
    if is_version_pattern(entry):
        return True, "version_reference"
    # 规则2: 含旧日期（超过1周）且为一次性事件
    if is_older_than_one_week(entry) and "一次性" in entry:
        return True, "older_than_one_week"
    return False, None


def run(dry_run: bool = False):
    start_time = datetime.now(timezone.utc)

    # 读记忆
    entries = read_entries(MEMORY_FILE)
    total = len(entries)

    # 无记忆 → 写心跳，跳过
    if total == 0:
        log_entry = {
            "timestamp": start_time.isoformat(),
            "status": "heartbeat",
            "reason": "no_memory",
            "duration_ms": 0,
        }
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print("巡检完成，无记忆条目")
        return

    # 逐条分类
    deleted = []
    kept = []
    seen_exact = set()
    exact_dupes = find_exact_duplicates(entries)

    for i, entry in enumerate(entries):
        should_delete, reason = classify_entry(entry)
        # 精确重复：保留第一个
        if entry in exact_dupes:
            first_pos = exact_dupes[entry][0]
            if i == first_pos:
                pass
            else:
                should_delete = True
                reason = "exact_duplicate"
                seen_exact.add(entry)

        if should_delete:
            deleted.append({"index": i, "entry": entry, "reason": reason})
        else:
            kept.append(entry)

    # 输出预览
    if dry_run:
        print("=== 预览模式（不执行删除）===")
        print(f"扫描条目总数: {total}")
        print(f"将删除: {len(deleted)} 条")
        print(f"将保留: {len(kept)} 条")
        if deleted:
            print("\n待删除条目:")
            for d in deleted:
                preview = d["entry"][:60] + ("..." if len(d["entry"]) > 60 else "")
                print(f"  [{d['reason']}] {preview}")
        if kept:
            print("\n将保留条目:")
            for e in kept:
                preview = e[:60] + ("..." if len(e) > 60 else "")
                print(f"  {preview}")
        return

    # 实际写入
    if deleted:
        MEMORY_FILE.write_text(ENTRY_DELIMITER.join(kept), encoding="utf-8")

    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    if len(deleted) == 0:
        log_entry = {
            "timestamp": start_time.isoformat(),
            "status": "clean",
            "total": total,
            "deleted_count": 0,
            "kept_count": len(kept),
            "duration_ms": duration_ms,
        }
    else:
        log_entry = {
            "timestamp": start_time.isoformat(),
            "status": "cleaned",
            "total": total,
            "deleted": deleted,
            "deleted_count": len(deleted),
            "kept_count": len(kept),
            "duration_ms": duration_ms,
        }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # 友好摘要
    print(f"🧹 记忆清理完成: 扫描 {total} 条，删除 {len(deleted)} 条，保留 {len(kept)} 条，耗时 {duration_ms}ms")
    for d in deleted:
        preview = d["entry"][:50] + ("..." if len(d["entry"]) > 50 else "")
        print(f"  删除 [{d['reason']}] {preview}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    run(dry_run=dry_run)
