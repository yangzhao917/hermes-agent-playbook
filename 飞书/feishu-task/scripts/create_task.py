#!/usr/bin/env python3
"""创建飞书任务，due 日期直接透传给 lark-cli（支持相对格式如 +2d）"""
import subprocess, json, sys

def get_my_open_id():
    result = subprocess.run(
        ["lark-cli", "contact", "+search-user", "--user-ids", "me", "--format", "json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    users = data.get("data", {}).get("users", [])
    if users:
        return users[0].get("open_id")
    return None

def create_task(summary: str, due: str = None, assignee: str = None, description: str = None, dry_run: bool = False):
    open_id = assignee or get_my_open_id()
    if not open_id:
        return {"error": "无法获取当前用户 open_id"}

    cmd = [
        "lark-cli", "task", "+create",
        "--summary", summary,
        "--assignee", open_id,
        "--format", "json"
    ]
    if due:
        cmd.extend(["--due", due])
    if description:
        cmd.extend(["--description", description])
    if dry_run:
        cmd.append("--dry-run")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {"ok": True, "dry_run": True, "output": result.stdout}

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
    except:
        return {"error": f"无法解析输出: {result.stdout[:200]}"}

    if data.get("ok"):
        guid = data.get("data", {}).get("guid", "")
        url = data.get("data", {}).get("url", "")
        return {"ok": True, "guid": guid, "url": url}
    else:
        return {"ok": False, "error": data.get("msg", "创建失败")}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--due", default=None, help="截止日期，支持 +2d 等相对格式")
    parser.add_argument("--assignee", default=None, help="open_id，不填则用当前用户")
    parser.add_argument("--description", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = create_task(
        summary=args.summary,
        due=args.due,
        assignee=args.assignee,
        description=args.description,
        dry_run=args.dry_run
    )

    if result.get("dry_run"):
        print("[dry-run] 任务将被创建：")
        print(result["output"])
        sys.exit(0)
    elif result.get("error"):
        print(f"❌ {result['error']}")
        sys.exit(1)
    elif result.get("ok"):
        print(f"✅ 任务已创建")
        print(f"   GUID: {result['guid']}")
        print(f"   链接: {result['url']}")
    else:
        print(f"❌ 创建失败: {result}")
        sys.exit(1)
