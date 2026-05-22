# Cron Reminder Workflow

## Design Pattern

Cron jobs call `lark-cli` directly in the prompt — no Python wrapper scripts. Token is managed by lark-cli's keychain (auto-refreshes), so the user's OAuth token is used and ALL personal calendar events are visible.

Workflow: Cron fires → AI receives prompt → calls `lark-cli calendar +agenda --start ... --end ... --format json` → lark-cli uses user's OAuth token from keychain → returns events → AI formats and delivers via WeChat.

```bash
# Query events (used directly in cron prompt)
lark-cli calendar +agenda --start "YYYY-MM-DD"T00:00:00+08:00" --end "YYYY-MM-DD"T23:59:59+08:00" --format json
```

## Jobs

### 1. Morning Reminder (07:00 daily, WeChat delivery)

```bash
schedule: "0 7 * * *"
deliver: origin (WeChat)
skill: lark-cli
prompt: >
  这是今天的日程，请用正常、友好的语气提醒用户。
  不要说"妈妈"、"宝贝"、"乖乖"等家庭角色用语。
  如果有活动祝他顺利/玩得开心，没有就说今天暂无安排。
  注意：如果日程包含凌晨时段（如01:00开始），要提醒用户注意休息。
```

### 2. Evening Review + Tomorrow Confirmation (22:00 daily, WeChat delivery) — ⚠️ Merged

```bash
schedule: "0 22 * * *"
deliver: origin (WeChat)
skill: lark-cli
prompt: >
  现在是晚上10点，用户需要回顾今日日程并确认明日安排。
  先 refresh token，再查今天和明天的日历。
  用正常友好的语气，先说今天完成了什么，再说明天有什么安排。
  不要说"妈妈"、"宝贝"、"乖乖"等家庭角色用语。
  如果明天没有日程，直接说"明天没有安排，好好休息～"
```

### 3. Daily Review Document Generation (22:30 daily) — ⚠️ Changed from 23:30 to 22:30

```yaml
schedule: "30 22 * * *"
deliver: origin (WeChat)
skill: lark-cli
```

**Template (fixed — do not change section titles, order, or wording):**
| Section | Type | Rule |
|---------|------|------|
| ✅ Completed | `✅ 完成事项` (table: 时间, 事项, 备注) | 🟥 Must |
| 📂 Projects Overview | Lightweight section at doc top | 🟨 Conditional — only when multiple parallel projects active today. Use 🟢🟡🔴 status markers |
| ⏰ Tomorrow | `⏰ 明日待办（日期）` (table: 时间, 事项) | 🟥 Must. If items rolled over from today, mark source |
| 📅 Future | `📅 后续安排` (table: 日期, 事项) | 🟧 Recommended |
| 💰 Follow-ups | `💰 待跟进` (list items) | 🟥 Must. Can prefix with ⏰ to indicate urgency/timing |
| 💡 Learned | `💡 今天学到的` (list items) | 🟧 If available. ⚠️ Use "今天学到的" not "今日新发现" |
| ⚡ Highlight/Mood | `⚡ 今日高光/感受` (optional, 1-2 sentences) | 🟨 Optional — only if user has a moment to share |

**User word preference (must follow):**
- Use **"待办"** not "代办"  (the user explicitly corrected this)
- Use **"今天学到的"** not "今日新发现" (the user explicitly asked for this change)
- Use **"待跟进"** as section title (💰 待跟进)

**Naming:** `YYYY-MM-DD-复盘总结`  
**Location:** 云空间 `HermesAgent/每日复盘/` (folder ID: A6KLfWMAQlZorydkeZscQkxanJf)

**Workflow:**
1. Token auto-refreshes with lark-cli
2. Check if doc exists via Drive API search
3. If not exists: create → move to folder → overwrite with content
4. If exists and needs update: overwrite or replace_range
5. If user deletes the review doc, pause the cron job to prevent auto-regeneration: `cronjob(action="pause", job_id=...)` and resume later with `cronjob(action="resume", job_id=...)`

**Official schedule rule:** Official hackathon/event schedules should NOT go in the review document. Add them to Feishu calendar instead via `lark-cli calendar +create`.

## Tone Rules (Mandatory)

**This user explicitly disallowed family-role persona in automated reminders.**

DO:
- Use direct, normal friendly tone
- Be concise — say "你有这些安排" not "我们来看看今天有什么"
- Use "你" not "宝贝/乖乖"

DO NOT:
- Do NOT use "妈妈" (mom), "姐姐" (sister), or any family role persona
- Do NOT use "宝贝" (baby), "乖乖" (darling), or pet names
- Do NOT use affectionate kaomoji or excessive emoji
- Do NOT roleplay as a family member

The model may spontaneously adopt these personas when trying to be warm. The prompt must explicitly forbid it.

## Weekend Hackathon Special Case

When events span weekend (e.g., hackathon Sat 08:00-Sun 17:00):
- Evening confirmation on Sat → confirm Sun schedule (morning + midnight events)
- Add 00:00 cron on Sun if any event starts at 01:00 AM

## Setting Up

1. Create cron jobs via `cronjob(action="create", ...)`
2. Verify with `cronjob(action="list")`
3. Test lark-cli calendar query manually: `lark-cli calendar +agenda --start "2026-05-22T00:00:00+08:00" --end "2026-05-22T23:59:59+08:00" --format json`

## Pitfalls

- Cron jobs deliver via the conversation origin (WeChat for this user)
- **⚠️ Do NOT use Python scripts to call Feishu HTTP API directly**: Raw tenant_access_token can ONLY see events created by the Hermes Agent app. Always use lark-cli in the cron prompt. If morning reminder shows empty, check: (1) `lark-cli auth status` shows token valid, (2) user has events on that day in their personal Feishu calendar.
- **⚠️ Token expiry**: If `401 Unauthorized` or `20026` (refresh token not found), re-run `lark-cli auth login --recommend --no-wait` → send URL to user → `lark-cli auth login --device-code <code>` to complete.
- Always specify tone constraints explicitly in the cron prompt. Models default to warm/family persona when given vague "friendly" instructions.
- When updating cron prompts, use `cronjob(action="update", job_id=..., prompt=...)` — the update takes effect on next run.
