#!/usr/bin/env python3
"""
friend-social-review 安装脚本
用法:
  python3 install.py              # 安装 skill
  python3 install.py --dry-run   # 预览
  python3 install.py --force      # 强制覆盖
  python3 install.py --uninstall  # 卸载（移除 skill 文件）

此 skill 为手动触发（对话中），不创建 cron 任务。
安装动作：将 SKILL.md 复制到 ~/.hermes/skills/friend-social-review/
"""
import shutil
import argparse
from pathlib import Path

SKILL_NAME = "friend-social-review"
SKILL_SRC = Path(__file__).parent / "SKILL.md"
SKILL_SRC_LEGACY = Path(__file__).parent.parent.parent / "skills" / SKILL_NAME / "SKILL.md"
VERSION_FILE = Path(__file__).parent / "VERSION"
SKILLS_DIR = Path.home() / ".hermes" / "skills"
SKILL_DST_DIR = SKILLS_DIR / SKILL_NAME
VERSION_MARKER = SKILL_DST_DIR / ".version"


def get_repo_version() -> str | None:
    if not VERSION_FILE.exists():
        return None
    return VERSION_FILE.read_text().strip()


def get_installed_version() -> str | None:
    if not VERSION_MARKER.exists():
        return None
    return VERSION_MARKER.read_text().strip()


def write_version_marker(version: str):
    SKILL_DST_DIR.mkdir(parents=True, exist_ok=True)
    VERSION_MARKER.write_text(version)


def do_install(force=False, dry_run=False):
    if not SKILL_SRC.exists():
        print(f"  错误：找不到 SKILL.md ({SKILL_SRC})")
        return False

    if dry_run:
        print(f"  [dry-run] 将安装 SKILL.md → {SKILL_DST_DIR}/")
        return True

    SKILL_DST_DIR.mkdir(parents=True, exist_ok=True)

    if SKILL_DST_DIR.exists() and not force:
        existing = SKILL_DST_DIR / "SKILL.md"
        if existing.exists() and existing.read_text() == SKILL_SRC.read_text():
            print(f"  {SKILL_NAME}: 已安装且无变化，跳过")
            return True

    shutil.copy2(SKILL_SRC, SKILL_DST_DIR / "SKILL.md")
    print(f"  {SKILL_NAME}: SKILL.md 已安装")
    return True


def do_uninstall(dry_run=False):
    if dry_run:
        print(f"  [dry-run] 将删除 {SKILL_DST_DIR}/")
        return

    if not SKILL_DST_DIR.exists():
        print(f"  {SKILL_NAME}: 未安装，跳过")
        return

    shutil.rmtree(SKILL_DST_DIR)
    print(f"  {SKILL_NAME}: 已卸载")


def main():
    parser = argparse.ArgumentParser(description="friend-social-review 安装脚本")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--uninstall", action="store_true",
                        help="卸载 skill（删除本地文件）")
    args = parser.parse_args()

    repo_version = get_repo_version()
    installed_version = get_installed_version()

    print("=== friend-social-review 安装 ===")
    print("  此 skill 为手动触发，不创建定时任务。")
    if repo_version:
        print(f"  仓库版本: {repo_version}")
    if installed_version:
        print(f"  已安装版本: {installed_version}")

    if args.uninstall:
        print()
        do_uninstall(dry_run=args.dry_run)
        print("\n=== 完成 ===")
        return

    # 版本检查
    if installed_version and repo_version and installed_version != repo_version:
        if args.force:
            print(f"  版本不一致，强制覆盖")
        else:
            print(f"  版本不一致（已安装 {installed_version}，仓库 {repo_version}）")
            print("  使用 --force 强制安装")
            if not args.dry_run:
                print("  跳过安装")
                return
    elif installed_version == repo_version and not args.force:
        print("  版本相同且已安装，无需更新")

    ok = do_install(force=args.force, dry_run=args.dry_run)

    if ok and not args.dry_run and repo_version:
        write_version_marker(repo_version)

    print("\n=== 完成 ===")
    print("  使用方式：直接对我说'帮我复盘一下xxx的人际关系'")
    if args.dry_run:
        print("  （dry-run，未实际安装）")


if __name__ == "__main__":
    main()
