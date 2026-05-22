# Feishu Calendar OAuth Flow

## Overview

Feishu uses a two-tier authorization model:
- **Tenant-level (app) token**: Read-only calendar access after admin grants `calendar:calendar:readonly` scope
- **User-level (OAuth) token**: Read + write access after user authorizes via OAuth

## Prerequisites

1. App has `calendar:calendar:readonly` or `calendar:calendar` scope in Developer Console
2. Admin has approved and **published a new version** (permissions don't take effect without publishing!)
3. A redirect URI is configured in App → Security Settings (e.g., `https://httpbin.org/get`)

## Step-by-Step Flow

### Step 1: Generate authorization URL

```python
APP_ID = os.environ["FEISHU_APP_ID"]
REDIRECT_URI = "https://httpbin.org/get"
SCOPE = "calendar:calendar"  # for write, or "calendar:calendar:readonly" for read-only
STATE = secrets.token_hex(16)

url = f"https://open.feishu.cn/open-apis/authen/v1/index"
url += f"?app_id={urllib.parse.quote(APP_ID)}"
url += f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
url += f"&scope={urllib.parse.quote(SCOPE)}"
url += f"&state={STATE}"
```

### Step 2: User authorizes in browser

User opens the URL, logs into Feishu, and clicks Authorize.

### Step 3: Capture authorization code

After authorization, browser redirects to:
```
https://httpbin.org/get?code={AUTH_CODE}&state={STATE}
```

The redirect page may show "404 page not found" or similar — this is **normal**. The auth code is in the URL parameters. Ask user to copy the full URL and paste it back.

### Step 4: Exchange code for tokens

```bash
POST https://open.feishu.cn/open-apis/authen/v1/access_token
Content-Type: application/json

{
  "grant_type": "authorization_code",
  "code": "{AUTH_CODE}",
  "app_id": "{APP_ID}",
  "app_secret": "{APP_SECRET}"
}
```

Response includes:
- `access_token` — valid ~6900 seconds (≈2 hours)
- `refresh_token` — valid ~2591700 seconds (≈30 days)
- `open_id` — user's Feishu Open ID
- `name` — user's display name

### Step 5: Use token to access user calendar

```bash
# List user's personal calendars
GET https://open.feishu.cn/open-apis/calendar/v4/calendars?page_size=50
Authorization: Bearer {user_access_token}
```

Response includes the user's primary calendar ID (different from the app's default calendar).

## Pitfalls

| Error | Cause | Fix |
|-------|-------|-----|
| `20029` "重定向 URL 有误" | OAuth redirect_uri not configured in app settings | Developer Console → Security → Add redirect URI |
| Code only usable once | OAuth code is single-use | Generate new authorization URL |
| Code returned but can't exchange | Code expired (~5 min validity) | Generate new URL quickly |
| `99991668` "Invalid access token" | user_access_token expired (~2 hours) | Refresh with `refresh_token` |
| `191002` "no calendar access_role" | Wrote to calendar with tenant_token instead of user_token | Use user_access_token for writes |
| `99991672` "Access denied" | App scope not enabled in Developer Console | Add scope AND publish new version |

## Token Refresh (Auto-Renewal)

To avoid re-authorization every 2 hours, use the `refresh_token`:

```bash
POST https://open.feishu.cn/open-apis/authen/v1/refresh_access_token
Content-Type: application/json

{
  "grant_type": "refresh_token",
  "refresh_token": "{REFRESH_TOKEN}",
  "app_id": "{APP_ID}",
  "app_secret": "{APP_SECRET}"
}
```

Response returns new `access_token` AND new `refresh_token`. Set up a weekly cron job to refresh before the 30-day refresh_token expiry.

## User Discovery

After first OAuth, discover the user's primary calendar ID:

1. Exchange code → get `user_access_token` + `open_id`
2. List calendars → find the calendar with `type: "primary"` (this is the user's personal calendar)
3. Save `open_id`, `calendar_id`, and `refresh_token` to `~/.hermes/feishu_user_token.json`
4. Update `feishu_calendar.py`'s `CALENDAR_ID` constant
