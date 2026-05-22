# Token Lifecycle Management

## Three Token Types

| Token | Source | Lifespan | Capability |
|-------|--------|----------|------------|
| `tenant_access_token` | App credentials (`FEISHU_APP_ID` + `FEISHU_APP_SECRET`) | 2 hours, auto-renewable | Reads (with granted scopes) |
| `user_access_token` | OAuth authorization code | ~6900s (≈2 hours) | Reads + writes (per user scope) |
| `refresh_token` | OAuth authorization code | ~2591700s (≈30 days) | Only for refreshing user_access_token |

## Auto-Refresh Strategy

Goal: Avoid manual OAuth re-authorization forever.

1. **Store** `refresh_token` + `open_id` + `calendar_id` in `~/.hermes/feishu_user_token.json`
2. **Weekly cron** (`0 3 * * 0`): Run `feishu_token.py refresh`
3. **On demand**: Any write operation calls `feishu_token.py get` before using token

## The feishu_token.py Script

```
~/.hermes/scripts/feishu_token.py
```

Commands:
- `refresh` — Fetch new access_token + refresh_token, update JSON file
- `get` — Print current access_token from file

### Refresh API

```bash
POST https://open.feishu.cn/open-apis/authen/v1/refresh_access_token
{
  "grant_type": "refresh_token",
  "refresh_token": "{saved_refresh_token}",
  "app_id": "{APP_ID}",
  "app_secret": "{APP_SECRET}"
}
```

Returns: new `access_token` + new `refresh_token` (replaces old one).

### Failure Recovery

**`refresh_token` expired** (error `20026: refresh token not found`):
- The `refresh_token` itself has a ~30-day validity; if `feishu_token.py refresh` is not run weekly, it expires
- Full OAuth re-authorization required: generate new auth URL → user authorizes → code exchange → save new `refresh_token`
- **Do not** try to re-use the expired `refresh_token` — it is permanently invalid

**Partial failure** (other errors):
- `10014` / `20035` → App Secret may have been reset in developer console → re-copy from credentials page
- `99991672` → scope not published → publish new version in developer console

## Token Expiry: 401 Unauthorized Pattern

When a Feishu API call returns `401 Unauthorized` (e.g. calendar events returns 0 + 401), the `user_access_token` has expired. The `refresh_token` may still be valid — try auto-refresh first:

```bash
python3 ~/.hermes/scripts/feishu_token.py refresh
```

If refresh also fails with `20026` (refresh_token not found / expired), full OAuth re-authorization is required:

```bash
# Step 1: initiate device auth (non-blocking)
lark-cli auth login --domain calendar,task --no-wait --json
# Returns: {"verification_url": "https://...", "device_code": "..."}

# Step 2: show URL verbatim to user (must be code block, no markdown, no rewriting)
# Example output:
# https://accounts.feishu.cn/oauth/v1/device/verify?flow_id=xxx&user_code=XXXX-XXXX

# Step 3: after user confirms auth complete, poll
lark-cli auth login --device-code <device_code> --json
```

**Key rules:**
- Show the `verification_url` exactly as returned — no markdown link formatting, no URL encoding/decoding
- Use `lark-cli auth login --no-wait` (not the blocking variant) so the agent can deliver the URL to the user in the same turn
- Do NOT run `--device-code` in the same turn as showing the URL — wait for the user to confirm they've completed auth

## Token Storage

```json
// ~/.hermes/feishu_user_token.json
{
  "access_token": "u-...",
  "refresh_token": "ur-...",
  "open_id": "ou_...",
  "calendar_id": "feishu.cn_...@group.calendar.feishu.cn",
  "expires_at": 1778775311
}
```

**Fields**:
- `access_token` — current user_access_token (valid ~2h), refreshed by `feishu_token.py refresh`
- `refresh_token` — long-lived (~30 days), used to get new access_token
- `open_id` — user identity, used for calendar queries
- `calendar_id` — user's primary calendar ID (discovered from `/calendars?page_size=50`, type=`primary`)
- `expires_at` — Unix timestamp when access_token expires (for pre-emptive refresh)

**⚠️ Always read `access_token` fresh** from this file before any API call — it changes on every refresh.
