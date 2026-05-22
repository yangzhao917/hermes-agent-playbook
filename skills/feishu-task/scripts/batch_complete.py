#!/usr/bin/env python3
"""
批量完成任务。
用法: python3 batch_complete.py --guids "guid1,guid2,guid3"
"""
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--guids", required=True, help="逗号分隔的 guid 列表")
    args = parser.parse_args()

    guids = [g.strip() for g in args.guids.split(",") if g.strip()]
    if not guids:
        print("没有有效的 guid")
        return

    success, failed = 0, 0
    for guid in guids:
        result = subprocess.run(
            ["lark-cli", "task", "+complete", guid, "--format", "json"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            success += 1
            print(f"✅ {guid[:12]}...")
        else:
            failed += 1
            print(f"❌ {guid[:12]}... - {result.stderr.strip()}")

    print(f"\n完成: {success}, 失败: {failed}")


if __name__ == "__main__":
    main()
