# Feishu API Quick Reference

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `FEISHU_APP_ID` | Internal app ID for the Feishu bot |
| `FEISHU_APP_SECRET` | Internal app secret for the Feishu bot |

## Common API Endpoints

### Auth

| Endpoint | Purpose |
|----------|---------|
| `POST /open-apis/auth/v3/tenant_access_token/internal` | Get app-level token |
| `POST /open-apis/authen/v1/access_token` | Exchange OAuth code for user token |
| `POST /open-apis/authen/v1/refresh_access_token` | Refresh user token using refresh_token |

### Calendar

| Endpoint | Purpose |
|----------|---------|
| `GET /open-apis/calendar/v4/calendars` | List calendars (min page_size: 50) |
| `GET /open-apis/calendar/v4/calendars/{id}/events` | List events (use unix timestamp) |
| `POST /open-apis/calendar/v4/calendars/{id}/events` | Create event |
| `PATCH /open-apis/calendar/v4/calendars/{id}/events/{eid}` | Update event |
| `DELETE /open-apis/calendar/v4/calendars/{id}/events/{eid}` | Delete event |
| `GET /open-apis/calendar/v4/calendars/primary` | Get current user's primary calendar |

### Doc / Wiki / Drive (requires additional scopes)

| Endpoint | Purpose |
|----------|---------|
| `GET /open-apis/docx/v1/documents/{id}/raw_content` | Get plain text of doc |
| `GET /open-apis/docx/v1/documents/{id}/blocks` | Get structured blocks of doc |
| `GET /open-apis/wiki/v2/spaces` | List wiki spaces |
| `GET /open-apis/wiki/v2/spaces/{id}/nodes` | List wiki nodes |
| `GET /open-apis/drive/v1/files` | List cloud space files |
| `GET /open-apis/drive/v1/files/{token}` | Get file metadata |
| `DELETE /open-apis/drive/v1/files/{token}?type=docx` | Delete a document (⚠️ not doc delete block) |
| `POST /open-apis/drive/v1/files/{token}/move` | Move file to folder |

## Required OAuth Scopes

| Scope | Permission | Token |
|-------|------------|-------|
| `calendar:calendar:readonly` | Read calendar events | tenant + user |
| `calendar:calendar` | CRUD calendar events | user only |
| `docx:document:readonly` | Read documents | tenant + user |
| `docx:document` | CRUD documents | user only |
| `wiki:wiki:readonly` | Read wiki/knowledge base | tenant + user |
| `wiki:wiki` | CRUD wiki | user only |
| `drive:drive` | Full cloud drive access | tenant + user |
| `drive:drive:readonly` | Read cloud drive files | tenant + user |
| `space:document:delete` | Delete documents | tenant + user |
| `search:search` | Search documents/messages | user only |

## Response Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| `99991672` | Scope not enabled. User must add scope AND publish new version |
| `99991663` | Tenant token used with wrong endpoint or missing scope |
| `99991668` | User token expired or invalid |
| `99991661` | Missing token entirely |
| `99992402` | Field validation (often page_size < 50 for calendar, or missing start_time/end_time) |
| `190014` | Wrong data type (e.g., ISO datetime instead of unix timestamp) |
| `191002` | Write attempted with read-only token (or tenant_token instead of user_token) |
| `193003` | Event already deleted |
| `20029` | OAuth redirect_uri not configured in app settings |
| `20003` | Authorization code expired or already used |
| `20035` | Invalid app secret (secret may have been regenerated) |
| `10014` | App secret invalid (same as 20035, on auth endpoint) |
| `1770003` | Document not found |
| `429` | Rate limited (too many requests) — lark-cli auto-retries

## URL Encoding

Calendar IDs contain `@` and `.` characters — always URL-encode them:

```python
import urllib.parse
encoded_cal_id = urllib.parse.quote(calendar_id, safe='')
```

For event queries, encode the calendar_id in the URL path even if it's in the middle.
