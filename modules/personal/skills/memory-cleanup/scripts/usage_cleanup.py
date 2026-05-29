#!/usr/bin/env python3
"""
清理 skills/.usage.json 中的过期记录。

规则：
- skill key 对应的 SKILL.md 文件已不存在 → 删除该条记录
- skill key 对应的目录不存在 → 删除该条记录
- 独立技能：~/.hermes/skills/{key}/SKILL.md
- 带子路径技能：~/.hermes/skills/{key}/SKILL.md

仅删除，确认只读用 --dry-run。
"""
import json
import os
import sys
from pathlib import Path

SKILLS_DIR = Path.home() / ".hermes" / "skills"
USAGE_FILE = SKILLS_DIR / ".usage.json"


def skill_path(key: str) -> Path:
    """解析 skill key 到 SKILL.md 路径。"""
    if "/" in key:
        return SKILLS_DIR / key / "SKILL.md"
    return SKILLS_DIR / key / "SKILL.md"


def run(dry_run: bool = False):
    if not USAGE_FILE.exists():
        print("❌ .usage.json 不存在")
        return

    with open(USAGE_FILE) as f:
        usage = json.load(f)

    removed = []
    remaining = {}
    for key, val in usage.items():
        path = skill_path(key)
        if path.exists():
            remaining[key] = val
        else:
            removed.append(key)

    print(f"扫描 {len(usage)} 条记录")
    print(f"保留 {len(remaining)} 条，删除 {len(removed)} 条")

    if removed:
        print("\n删除:")
        for r in removed:
            print(f"  - {r}")

    if dry_run:
        print("\n[预览模式，未执行删除]")
        return

    with open(USAGE_FILE, "w") as f:
        json.dump(remaining, f, indent=2, ensure_ascii=False)

    print("\n✅ .usage.json 已更新")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    run(dry_run=dry_run)