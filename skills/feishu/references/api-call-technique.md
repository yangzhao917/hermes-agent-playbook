# Feishu API Call Techniques

## 🌟 Preferred: Python `urllib.request` in `execute_code`

Use this approach for ALL Feishu API calls. It avoids two common pitfalls:

### Pitfall 1: Stale bash working directory
The `terminal` tool may inherit a stale working directory (`/tmp/openclaw-x` or similar), causing `FileNotFoundError` on all bash commands.

### Pitfall 2: `.env` not sourced in bash subprocesses
`FEISHU_APP_ID` and `FEISHU_APP_SECRET` live in `~/.hermes/.env`. Bash subprocesses from `terminal` or `subprocess.run()` do **not** source this file — `os.environ.get("FEISHU_APP_ID")` returns empty.

### Solution: `execute_code` + `urllib.request`

The Hermes agent runtime loads `~/.hermes/.env` into the agent process environment. **`execute_code` inherits this environment**, so `os.environ` works correctly.

```python
import json, urllib.request

# ✅ FEISHU_APP_ID and FEISHU_APP_SECRET are available here
app_id = os.environ.get("FEISHU_APP_ID")
app_secret = os.environ.get("FEISHU_APP_SECRET")

# Build request
body = json.dumps({...}).encode()
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read())
```

## Token Refresh

```python
url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
body = json.dumps({
    "grant_type": "refresh_token",
    "refresh_token": saved_refresh_token,
    "app_id": app_id,
    "app_secret": app_secret
}).encode()
```

Response `code: 0` on success. The new `access_token` and `refresh_token` are in `data.access_token` / `data.refresh_token`.

## Calendar Query

```python
url = f"https://open.feishu.cn/open-apis/calendar/v4/calendars/{calendar_id}/events?page_size=50&start_time={start_ts}&end_time={end_ts}"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
with urllib.request.urlopen(req, timeout=10) as resp:
    events = json.loads(resp.read())
```

**⚠️** `start_time`/`end_time` must be Unix timestamps in seconds (not ISO 8601 strings).

## Fallback: bash `curl`

Only use when you need to pipe output or chain commands. If env vars aren't found, hardcode them inline (but prefer `execute_code`).
