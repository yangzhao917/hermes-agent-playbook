#!/usr/bin/env python3
"""
memory-cleanup 安装脚本
用法:
  python3 install.py              # 安装（如已安装且版本相同则跳过）
  python3 install.py --dry-run     # 预览安装动作
  python3 install.py --force       # 强制安装（无视版本，强制覆盖）
"""
import subprocess
import argparse
from pathlib import Path

SCRIPT_NAME = "memory_cleanup.py"
SCRIPT_SRC = Path(__file__).parent / "scripts" / SCRIPT_NAME
SCRIPT_DST = Path.home() / ".hermes" / "scripts" / SCRIPT_NAME
VERSION_FILE = Path(__file__).parent / "VERSION"
VERSION_MARKER = SCRIPT_DST.parent / f"{SCRIPT_NAME}.version"


def get_repo_version() -> str | None:
    if not VERSION_FILE.exists():
        return None
    return VERSION_FILE.read_text().strip()


def get_installed_version() -> str | None:
    if not VERSION_MARKER.exists():
        return None
    return VERSION_MARKER.read_text().strip()


def write_version_marker(version: str):
    VERSION_MARKER.write_text(version)


def list_existing():
    try:
        import json
        r = subprocess.run(
            ["hermes", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            return {j.get("name") for j in data.get("jobs", [])}
    except Exception:
        pass
    return set()


def ensure_script(force=False, dry_run=False):
    if dry_run:
        print(f"  [dry-run] 将安装脚本 → {SCRIPT_DST}")
        return

    SCRIPT_DST.parent.mkdir(parents=True, exist_ok=True)
    content = SCRIPT_SRC.read_text()

    if SCRIPT_DST.exists() and SCRIPT_DST.read_text() == content:
        print(f"  {SCRIPT_NAME}: 已安装且无变化，跳过")
        return

    SCRIPT_DST.write_text(content)
    print(f"  {SCRIPT_NAME}: 已安装")


def ensure_cron(force=False, dry_run=False):
    job_name = "每周记忆清理"
    existing = list_existing()

    if job_name in existing:
        if dry_run:
            print(f"  [dry-run] cron job '{job_name}' 已存在，跳过")
        else:
            print(f"  {job_name}: 已存在，跳过")
        return

    if dry_run:
        print(f"  [dry-run] 将创建 cron job '{job_name}'")
        return

    cmd = [
        "hermes", "cron", "create",
        "0 0 * * 0",
        "--name", job_name,
        "--deliver", "origin",
        "--no-agent",
        "--script", SCRIPT_NAME,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {job_name}: 创建成功")
    else:
        print(f"  {job_name}: 创建失败")
        print(f"    {r.stderr[:200]}")


def main():
    parser = argparse.ArgumentParser(description="memory-cleanup 安装脚本")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览，不执行实际安装")
    parser.add_argument("--force", action="store_true",
                        help="强制安装（覆盖已安装版本）")
    args = parser.parse_args()

    repo_version = get_repo_version()
    installed_version = get_installed_version()

    print("=== memory-cleanup 安装 ===")
    if repo_version:
        print(f"  仓库版本: {repo_version}")
    if installed_version:
        print(f"  已安装版本: {installed_version}")

    # 版本检查
    if installed_version and repo_version and installed_version != repo_version:
        if args.force:
            print(f"  版本不一致，强制覆盖（已安装 {installed_version} → 仓库 {repo_version}）")
        else:
            print(f"  版本不一致（已安装 {installed_version}，仓库 {repo_version}）")
            print("  使用 --force 强制安装，或手动拉取仓库更新后再安装")
            if not args.dry_run:
                print("  跳过安装")
                return
    elif installed_version == repo_version and not args.force:
        print("  版本相同且已安装，无需更新")

    print()
    ensure_script(force=args.force, dry_run=args.dry_run)
    print()
    ensure_cron(force=args.force, dry_run=args.dry_run)

    # 写入版本标记
    if not args.dry_run and repo_version:
        write_version_marker(repo_version)

    print("\n=== 完成 ===")
    if args.dry_run:
        print("（dry-run，未实际创建）")
    else:
        print("查看任务: hermes cron list")


if __name__ == "__main__":
    main()
