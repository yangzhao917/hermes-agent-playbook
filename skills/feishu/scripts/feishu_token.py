#!/usr/bin/env python3
"""Feishu token auto-refresh script.
Refreshes the user access_token using the saved refresh_token.
Run periodically (e.g., weekly) via cron to keep tokens alive forever.

Usage:
    python3 feishu_token.py refresh   # Refresh both tokens
    python3 feishu_token.py get       # Print current access_token
"""

import json
import os
import sys
import urllib.request

TOKEN_FILE = os.path.expanduser("~/.hermes/feishu_user_token.json")
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")


def refresh_token():
    """Refresh the access_token and refresh_token using the saved refresh_token."""
    if not os.path.exists(TOKEN_FILE):
        print("ERROR: No token file found. Need initial OAuth.")
        return False

    with open(TOKEN_FILE) as f:
        data = json.load(f)

    old_refresh = data.get("refresh_token")
    if not old_refresh:
        print("ERROR: No refresh_token found in token file.")
        return False

    url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": old_refresh,
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }).encode()

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        if result.get("code") == 0:
            d = result["data"]
            data["access_token"] = d["access_token"]
            data["refresh_token"] = d["refresh_token"]
            data["expires_at"] = d.get("expires_in", 6900)
            with open(TOKEN_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"✅ Token refreshed. New refresh_token saved.")
            return True
        else:
            print(f"❌ Refresh failed: {result}")
            return False
    except Exception as e:
        print(f"⚠️ Refresh failed: {e}")
        return False


def get_access_token():
    """Get the current access_token from the saved file."""
    if not os.path.exists(TOKEN_FILE):
        return ""
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    return data.get("access_token", "")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "refresh"
    if cmd == "refresh":
        refresh_token()
    elif cmd == "get":
        token = get_access_token()
        if token:
            print(token)
        else:
            print("ERROR: No token available")
            sys.exit(1)
