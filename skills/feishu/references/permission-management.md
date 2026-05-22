# Feishu Permission Management - Key Lessons

## The #1 Root Cause of "权限未生效"

Users add permissions in the developer console, but **forget to publish a new version**.

```
Developer Console → 权限管理 → 添加权限 ✓
                          → 版本管理与发布 → 发布新版本 ← 漏了这一步 ❌
```

Without publishing, all newly added scopes (both tenant and user) return `99991672` regardless of OAuth re-authorization.

## Permission Type Cheatsheet

| Need this... | Add as... | Then... |
|---|---|---|
| Delete documents via API | Tenant scope: `drive:drive` or `space:document:delete` | Publish new version |
| List user's cloud files | User OAuth scope: `drive:drive:readonly` | Publish + re-authorize via OAuth |
| Read wiki spaces | Tenant scope: `wiki:wiki:readonly` | Publish new version |
| Create/move wiki nodes | User OAuth scope: `wiki:node:create`, `wiki:node:move` | Publish + re-authorize |
| Update wiki node title | User OAuth scope: `wiki:node:update` | Must be explicitly requested in OAuth URL; re-authorize |
| Delete wiki node | User OAuth scope: `wiki:node:delete` | Must be explicitly requested in OAuth URL; re-authorize |
| Add wiki space members | User OAuth scope: `wiki:member:create` | Publish + re-authorize |
| Calendar read | Tenant scope: `calendar:calendar:readonly` | Publish new version |
| Calendar CRUD | User OAuth scope: `calendar:calendar` | Publish + re-authorize |

## Wiki Space: App Must Be Added as Member

Even if an app has the correct wiki scopes, an app token (tenant_access_token) **cannot** list or operate on user wiki spaces unless the app is explicitly added as a member of that wiki space.

**Symptom:** `wiki spaces` returns empty list with app token, or `wiki update` returns 404.

**Fix (option A — recommended):** In Feishu, open the target wiki space → ⋯ → Space Settings → Member Management → Add app "Hermes Agent" with editor permissions.

**Fix (option B — programmatic):** Use user token's `wiki member add` command:
```bash
lark-cli wiki members create <space_id> \
  --member-type email \
  --member-id app@yourcompany.com \
  --role admin
```

## App Secret Reset Trap

**Symptom:** Previously working `tenant_access_token` suddenly returns `code: 10014` ("app secret invalid").

**Likely cause:** User regenerated App Secret while in Developer Console (sometimes permissions screens trigger this). The old secret cached in config/env is now stale.

**Fix:** Ask user to go to Developer Console → 凭证与基础信息 → copy the current App Secret.

## Multi-Scope OAuth URL Pattern

```
base: https://open.feishu.cn/open-apis/authen/v1/index
params:
  app_id: cli_xxx
  redirect_uri: https://httpbin.org/get
  scope: scope1,scope2,scope3  # comma-separated, no URL-encoding needed
  state: hermes_auth
```

Example URL:
```
https://open.feishu.cn/open-apis/authen/v1/index?app_id=cli_xxx&redirect_uri=https://httpbin.org/get&scope=calendar:calendar:readonly,calendar:calendar,drive:drive:readonly,wiki:wiki:readonly&state=hermes_auth
```

After user authorizes, they're redirected to `redirect_uri?code=XXX&state=YYY`. The `code` is in the URL. Exchange it via:

```python
POST https://open.feishu.cn/open-apis/authen/v1/access_token
body: {"app_id":..., "app_secret":..., "grant_type":"authorization_code", "code":...}
```

## Delete Document via Drive API

`lark-cli drive +delete --type docx` requires 2 args (doc_id + block_id) and deletes blocks, NOT the entire document.

To delete an entire docx document:

```bash
curl -s -X DELETE "https://open.feishu.cn/open-apis/drive/v1/files/{DOC_TOKEN}?type=docx" \
  -H "Authorization: Bearer {TOKEN}"
```

Requires tenant scope: `drive:drive` or `space:document:delete` (must publish new version).

## curl with Special Characters in JSON

When the App Secret contains characters that break shell quoting (`$`, `"`, `!`, etc.), prefer Python's `subprocess.run()` with `json.dumps()` over embedded bash variable expansion:

```python
# GOOD: no shell quoting issues
import subprocess, json
result = subprocess.run(
    ["curl", "-s", "-X", "POST", "https://open.feishu.cn/open-apis/authen/v1/access_token",
     "-H", "Content-Type: application/json",
     "-d", json.dumps({"app_id": app_id, "app_secret": secret, "code": code})],
    capture_output=True, text=True
)

# BAD: shell may mangle special characters in secret
curl -s -X POST '...' -d '{"app_secret":"$SECRET"}'  # ❌ bash expands $SECRET
```
