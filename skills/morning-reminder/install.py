#!/usr/bin/env python3
"""
morning-reminder 安装脚本
用法: python3 install.py
"""
import json
import subprocess
import argparse
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent.parent.resolve()
SCRIPT_NAME = "morning_reminder.py"
SCRIPT_SRC = Path(__file__).parent / "scripts" / SCRIPT_NAME
SCRIPT_DST = Path.home() / ".hermes" / "scripts" / SCRIPT_NAME


def ensure_script():
    print("[1/3] 安装脚本...")
    SCRIPT_DST.parent.mkdir(parents=True, exist_ok=True)
    content = SCRIPT_SRC.read_text()
    if SCRIPT_DST.exists() and not SCRIPT_DST.is_symlink():
        existing = SCRIPT_DST.read_text()
        if existing == content:
            print(f"  {SCRIPT_NAME}: 已安装且无变化，跳过")
            return
        print(f"  {SCRIPT_NAME}: 内容有变化，将更新")
    SCRIPT_DST.write_text(content)
    print(f"  {SCRIPT_NAME}: 已安装")


def list_existing():
    try:
        r = subprocess.run(["hermes", "cron", "list", "--json"],
                          capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            data = json.loads(r.stdout)
            return {j.get("name") for j in data.get("jobs", [])}
    except Exception:
        pass
    return set()


def create_cron(dry_run=False):
    print("\n[2/3] 创建定时任务...")
    job_name = "每日晨间日程提醒"
    existing = list_existing()

    if job_name in existing:
        print(f"  {job_name}: 已存在，跳过")
        return

    if dry_run:
        print(f"  {job_name}: [dry-run] 会创建")
        return

    cmd = [
        "hermes", "cron", "create",
        "0 7 * * *",
        "--name", job_name,
        "--deliver", "origin",
        "--skill", "lark-cli",
        "--skill", "morning-reminder",
        "--script", SCRIPT_NAME,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {job_name}: 创建成功")
    else:
        print(f"  {job_name}: 创建失败")
        print(f"    {r.stderr[:200]}")


def main():
    parser = argparse.ArgumentParser(description="morning-reminder 安装脚本")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=== morning-reminder 安装 ===")
    ensure_script()
    create_cron(dry_run=args.dry_run)
    print("\n[3/3] 完成！")
    if args.dry_run:
        print("（dry-run，未实际创建）")
    else:
        print("查看任务: hermes cron list")


if __name__ == "__main__":
    main()
