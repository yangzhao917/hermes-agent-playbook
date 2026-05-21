#!/usr/bin/env python3
"""
Hermes Agent 定时任务一键安装脚本
用法: python3 install.py

支持 dry-run: python3 install.py --dry-run
"""
import glob
import json
import os
import subprocess
import argparse
from pathlib import Path

REPO_DIR = Path(__file__).parent.resolve()
HERMES_DIR = Path.home() / ".hermes"
SCRIPTS_DIR = HERMES_DIR / "scripts"
AGENT_CONF = HERMES_DIR / "agent.conf"


def get_user_name():
    conf = {}
    if AGENT_CONF.exists():
        for line in AGENT_CONF.read_text().splitlines():
            if "=" in line:
                k, v = line.strip().split("=", 1)
                conf[k.strip()] = v.strip().strip('"')
    return conf.get("user_name", "你的名字")


def get_feishu_folder():
    conf = {}
    if AGENT_CONF.exists():
        for line in AGENT_CONF.read_text().splitlines():
            if "=" in line:
                k, v = line.strip().split("=", 1)
                conf[k.strip()] = v.strip().strip('"')
    return conf.get("feishu_folder", "hermesAgent/每日复盘/")


def render_script(src_path, user_name, feishu_folder=None):
    content = src_path.read_text(encoding="utf-8")
    content = content.replace("{{USER_NAME}}", user_name)
    if feishu_folder:
        content = content.replace("{{FEISHU_FOLDER}}", feishu_folder)
    return content


def ensure_scripts():
    print("\n[1/4] 安装 scripts...")
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    user_name = get_user_name()
    feishu_folder = get_feishu_folder()

    for src in glob.glob(str(REPO_DIR / "scripts" / "*.py")):
        name = Path(src).name
        dst = SCRIPTS_DIR / name
        rendered = render_script(Path(src), user_name, feishu_folder)

        if dst.exists() and not dst.is_symlink():
            existing = dst.read_text(encoding="utf-8")
            if existing == rendered:
                print(f"  {name}: 已安装且无变化，跳过")
                continue
            print(f"  {name}: 内容有变化，将更新")
        elif dst.is_symlink():
            print(f"  {name}: 已有软链接，将替换为渲染版本")

        dst.write_text(rendered, encoding="utf-8")
        print(f"  {name}: 已安装")


def check_skills():
    print("\n[2/4] 检查依赖 skills...")
    try:
        result = subprocess.run(
            ["hermes", "skills", "list"],
            capture_output=True, text=True, timeout=10
        )
        installed = set(result.stdout.splitlines())
    except Exception:
        installed = set()

    for skill in ["lark-cli", "morning-reminder", "daily-review", "memory-cleanup"]:
        if skill in installed:
            print(f"  {skill}: 已安装")
        else:
            print(f"  {skill}: 未安装（提示: hermes skills install {skill}）")


def list_existing_crons():
    try:
        result = subprocess.run(
            ["hermes", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {j.get("name") for j in data.get("jobs", [])}
    except Exception:
        pass
    return set()


def create_crons(dry_run=False):
    print("\n[3/4] 创建定时任务...")
    existing_names = list_existing_crons()

    jobs = [
        {
            "name": "每日晨间日程提醒",
            "schedule": "0 7 * * *",
            "skills": ["lark-cli", "morning-reminder"],
            "skill": "lark-cli",
            "script": "morning_reminder.py",
        },
        {
            "name": "每日复盘总结生成",
            "schedule": "30 23 * * *",
            "skills": ["lark-cli", "daily-review"],
            "skill": "lark-cli",
            "workdir": str(HERMES_DIR),
            "script": "daily_review.py",
        },
        {
            "name": "每周记忆清理",
            "schedule": "0 0 * * 0",
            "skills": [],
            "skill": None,
            "no_agent": True,
            "script": "memory_cleanup.py",
        },
    ]

    for job in jobs:
        if job["name"] in existing_names:
            print(f"  {job['name']}: 已存在，跳过")
            continue

        if dry_run:
            print(f"  {job['name']}: [dry-run] 会创建")
            continue

        cmd = [
            "hermes", "cron", "create",
            job["schedule"],
            "--name", job["name"],
            "--deliver", "origin",
        ]
        for s in job.get("skills", []):
            cmd += ["--skill", s]
        if job.get("skill"):
            cmd += ["--skill", job["skill"]]
        if job.get("workdir"):
            cmd += ["--workdir", job["workdir"]]
        if job.get("no_agent"):
            cmd += ["--no-agent"]
        if job.get("script"):
            cmd += ["--script", job["script"]]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  {job['name']}: 创建成功")
        else:
            print(f"  {job['name']}: 创建失败")
            print(f"    {result.stderr[:200]}")


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent 定时任务安装脚本")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不执行")
    args = parser.parse_args()

    print("=== Hermes Agent 定时任务安装 ===")
    print(f"仓库目录: {REPO_DIR}")
    print(f"安装目录: {HERMES_DIR}")

    ensure_scripts()
    check_skills()
    create_crons(dry_run=args.dry_run)

    print("\n[4/4] 完成！")
    if args.dry_run:
        print("（以上为 dry-run 模式，未实际创建任务）")
    else:
        print("查看任务列表: hermes cron list")
    print("""
提示:
  - 上述任务默认推送到当前对话（origin）
  - 飞书文件夹路径可编辑 ~/.hermes/scripts/daily_review.py 中的 FEISHU_FOLDER 常量修改
  - 用户名称从 ~/.hermes/agent.conf 读取（user_name 字段）
""")


if __name__ == "__main__":
    main()
