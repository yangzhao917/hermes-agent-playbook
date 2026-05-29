---
name: agent-reach
description: "Search and read 14 platforms: Twitter/X, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu (小红书), Douyin (抖音), Weibo (微博), WeChat Articles (公众号), LinkedIn, Instagram, RSS, Exa web search, and any URL. Use when: user asks to search a platform, read a URL, research a topic, or configure a channel. Triggers: 搜/查/看/读/找 + platform name, or any shared URL from supported platforms."
metadata:
  openclaw:
    homepage: https://github.com/Panniantong/Agent-Reach
---

# Agent Reach — Usage Guide

Upstream tools for 13+ platforms. Call them directly.

Run `agent-reach doctor` to check which channels are available.

## ⚠️ Workspace Rules

**Never create files in the agent workspace.** Use `/tmp/` for temporary output and `~/.agent-reach/` for persistent data.

## Web — Any URL

```bash
curl -s "https://r.jina.ai/URL"
```

## Web Search (Exa)

```bash
mcporter call 'exa.web_search_exa(query: "query", numResults: 5)'
mcporter call 'exa.get_code_context_exa(query: "code question", tokensNum: 3000)'
```

## Twitter/X (xreach)

```bash
xreach search "query" -n 10 --json          # search
xreach tweet URL_OR_ID --json                # read tweet (supports /status/ and /article/ URLs)
xreach tweets @username -n 20 --json         # user timeline
xreach thread URL_OR_ID --json               # full thread
```

## YouTube (yt-dlp)

```bash
yt-dlp --dump-json "URL"                     # video metadata
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"
                                             # download subtitles, then read the .vtt file
yt-dlp --dump-json "ytsearch5:query"         # search
```

## Bilibili (yt-dlp)

```bash
yt-dlp --dump-json "https://www.bilibili.com/video/BVxxx"
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --convert-subs vtt --skip-download -o "/tmp/%(id)s" "URL"
```

> Server IPs may get 412. Use `--cookies-from-browser chrome` or configure proxy.

## Reddit

```bash
curl -s "https://www.reddit.com/r/SUBREDDIT/hot.json?limit=10" -H "User-Agent: agent-reach/1.0"
curl -s "https://www.reddit.com/search.json?q=QUERY&limit=10" -H "User-Agent: agent-reach/1.0"
```

> Server IPs may get 403. Search via Exa instead, or configure proxy.

## GitHub (gh CLI)

```bash
gh search repos "query" --sort stars --limit 10
gh repo view owner/repo
gh search code "query" --language python
gh issue list -R owner/repo --state open
gh issue view 123 -R owner/repo
```

## 小红书 / XiaoHongShu (xiaohongshu-mcp-steve)

> ⚠️ Requires three tokens + standalone MCP server install. Not available via mcporter.

**Required tokens** (all three, from DevTools Network panel):
- `XIAOHONGSHU_COOKIE` — browser cookie (Netscape format string)
- `XIAOHONGSHU_XS` — from Cookie field, `xs=...` value
- `XIAOHONGSHU_XS_COMMON` — from Cookie field, `xs_common=...` value

> **Pitfall**: Cookie-Editor export JSON `data` field does NOT contain `xs`/`xs_common`. Must extract from DevTools → Network → any `edith.xiaohongshu.com` request → Request Headers → Cookie. Without these, API returns "当前账号存在异常" (anti-scraping block, not account issue).

**Install + run**:
```bash
cd /tmp && mkdir -p xhs-mcp && cd xhs-mcp && npm init -y && npm install xiaohongshu-mcp-steve
XIAOHONGSHU_COOKIE="..." XIAOHONGSHU_XS="..." XIAOHONGSHU_XS_COMMON="..." \
  node /tmp/xhs-mcp/node_modules/xiaohongshu-mcp-steve/dist/index.js
```

**Call via stdio JSON-RPC** (python subprocess):
```python
import subprocess, json, os
cookie = os.environ.get('XIAOHONGSHU_COOKIE', '')
xs = os.environ.get('XIAOHONGSHU_XS', '')
xs_common = os.environ.get('XIAOHONGSHU_XS_COMMON', '')
env = {**os.environ, 'XIAOHONGSHU_COOKIE': cookie, 'XIAOHONGSHU_XS': xs, 'XIAOHONGSHU_XS_COMMON': xs_common}
init_req = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"hermes","version":"1.0.0"}}}) + "\n"
search_req = json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_notes","arguments":{"keyword":"黑客松","page":1,"page_size":10}}}) + "\n"
proc = subprocess.Popen(["node", "/tmp/xhs-mcp/node_modules/xiaohongshu-mcp-steve/dist/index.js"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
out, _ = proc.communicate(input=(init_req + search_req).encode(), timeout=30)
print(out.decode())
```

**Known response states**:
- `total: 0, status: 200` → tokens valid, search limited/rate-limited (try different keywords)
- `code: 461, msg: "当前笔记暂时无法浏览"` → note deleted/private, no recovery
- `error.message: "当前账号存在异常"` → `xs`/`xs_common` missing from env

**Fallback**: `curl -s "https://r.jina.ai/https://xhslink.com/m/USER_ID"` for public profile only. Note details require MCP.

## 抖音 / Douyin (mcporter)

```bash
mcporter call 'douyin.parse_douyin_video_info(share_link: "https://v.douyin.com/xxx/")'
mcporter call 'douyin.get_douyin_download_link(share_link: "https://v.douyin.com/xxx/")'
```

> No login needed.

## 微信公众号 / WeChat Articles

**Search** (miku_ai):
```python
python3 -c "
import asyncio
from miku_ai import get_wexin_article
async def s():
    for a in await get_wexin_article('query', 5):
        print(f'{a[\"title\"]} | {a[\"url\"]}')
asyncio.run(s())
"
```

**Read** (Camoufox — bypasses WeChat anti-bot):
```bash
cd ~/.agent-reach/tools/wechat-article-for-ai && python3 main.py "https://mp.weixin.qq.com/s/ARTICLE_ID"
```

> WeChat articles cannot be read with Jina Reader or curl. Must use Camoufox.

## LinkedIn (mcporter)

```bash
mcporter call 'linkedin.get_person_profile(linkedin_url: "https://linkedin.com/in/username")'
mcporter call 'linkedin.search_people(keyword: "AI engineer", limit: 10)'
```

Fallback: `curl -s "https://r.jina.ai/https://linkedin.com/in/username"`

## RSS (feedparser)

## RSS

```python
python3 -c "
import feedparser
for e in feedparser.parse('FEED_URL').entries[:5]:
    print(f'{e.title} — {e.link}')
"
```

## Troubleshooting

- **Channel not working?** Run `agent-reach doctor` — shows status and fix instructions.
- **Twitter fetch failed?** Ensure `undici` is installed: `npm install -g undici`. Configure proxy: `agent-reach configure proxy URL`.

## Setting Up a Channel ("帮我配 XXX")

If a channel needs setup (cookies, Docker, etc.), fetch the install guide:
https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md

User only provides cookies. Everything else is your job.
