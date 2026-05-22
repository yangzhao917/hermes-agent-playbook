# Calendar API Reference

## Base URL

```
https://open.feishu.cn/open-apis/calendar/v4
```

## Authentication

Two token types:
- `Authorization: Bearer {tenant_access_token}` — for reads only, auto-refreshable via app credentials
- `Authorization: Bearer {user_access_token}` — for reads + writes, needs refresh_token management

## List Calendars

```bash
GET /calendars?page_size=50
```

**⚠️ Critical**: `page_size` minimum is **50**. Values below 50 return error `99992402` ("the min value is 50").

Response includes `calendar_list` array. Look for `type: "primary"` for the user's personal calendar.

## Get Events

```bash
GET /calendars/{calendar_id}/events?page_size=50&start_time={unix_ts}&end_time={unix_ts}
```

**⚠️ Critical**: `start_time`/`end_time` must be **Unix timestamps in seconds**. ISO 8601 strings like `2026-05-15T20:00:00+08:00` return error `190014` ("data type of the start_time field is incorrect").

## Create Event

```bash
POST /calendars/{calendar_id}/events
Content-Type: application/json
Authorization: Bearer {user_access_token}

{
  "summary": "Event Title",
  "description": "Optional description",
  "start_time": { "date": "2026-05-15" },  # all-day
  "end_time": { "date": "2026-05-16" },    # exclusive end
  "status": "tentative",
  "reminders": [{"minutes": 120}]
}
```

**⚠️ Must use `user_access_token`** (tenant_token returns `191002` "no calendar access_role").

## Update Event (PATCH)

```bash
PATCH /calendars/{calendar_id}/events/{event_id}
Content-Type: application/json
Authorization: Bearer {user_access_token}

{
  "summary": "Updated Title",
  "start_time": { "date": "2026-05-15" },
  "end_time": { "date": "2026-05-16" }
}
```

## Delete Event

```bash
DELETE /calendars/{calendar_id}/events/{event_id}
Authorization: Bearer {user_access_token}
```

## All-Day Event Behavior

All-day events use the `date` field (not `datetime`). The end date is **exclusive** (iCal standard):

- Single day on May 15: `start={"date":"2026-05-15"}`, `end={"date":"2026-05-16"}`
- The API **stores** the end date as start+1 day for a 1-day event
- Multi-day: `start={"date":"2026-05-15"}`, `end={"date":"2026-05-17"}` spans May 15-16

When querying by date range, events appear in any day where their duration overlaps with the query range (including the end date boundary).

## Event Fields

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string \| null | Event title — **can be null for cancelled events** |
| `description` | string | Event description |
| `start_time`/`end_time` | object | `{"date": "YYYY-MM-DD"}` for all-day, `{"timestamp": "UNIX_SEC", "timezone": "Asia/Shanghai"}` for timed |
| `status` | string | `confirmed` / `tentative` / **`cancelled`** |
| `reminders` | array | `[{"minutes": N}]` — minutes before event |
| `vchat.meeting_url` | string | Feishu VC meeting link |
| `location` | string | Physical location |
| `free_busy_status` | string | `busy` or `free` |
| `attendee_ability` | string | e.g. `can_invite_others` |

## ⚠️ Cancelled Events: Filter by `status`

**Cancelled events are real API objects** — they remain in query results even after deletion. Two problems:
1. `summary` is `null` → displays as "无标题"
2. They still occupy list positions

**Always filter**:
```python
for ev in events:
    if ev.get("status") == "cancelled":
        continue
    # process valid event
```

## ⚠️ Time Parsing: `timestamp` vs `date`

```python
st = ev.get("start_time", {})
if "date" in st:
    # All-day event: "2026-05-15"
    time_str = st["date"]
else:
    ts = st.get("timestamp")
    if ts:
        dt = datetime.fromtimestamp(int(ts), tz=timezone(timedelta(hours=8)))
        time_str = dt.strftime("%H:%M")
    else:
        time_str = ""
```

**Common mistake**: treating `timestamp` as a date string — it is a Unix epoch integer.

## Event ID Format

Event IDs end with `_0` for non-recurring events (e.g., `bf2837a9-9556-4787-ad18-b050bea76742_0`). Recurring event instances may have different suffixes.
