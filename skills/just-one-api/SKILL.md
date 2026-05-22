---
name: just-one-api
category: social-media
description: Just One API 统一数据平台，支持小红书、抖音、微博、哔哩哔哩、微信等平台的搜索、用户资料、笔记/视频详情等接口。
trigger: "调用 Just One API / justoneapi / 小红书数据 / 抖音数据 / 微博热搜 / 跨平台搜索 / 查询XX在全网的影响力 / XX品牌声量 / 活动传播效果 / 社交媒体热度"
---

# Just One API Skill

## 基础信息

- **官网**: https://justoneapi.com
- **文档**: https://docs.justoneapi.com/zh/
- **Python SDK**: https://github.com/justoneapi/justoneapi-python
- **Token 获取**: https://dashboard.justoneapi.com/zh

## Base URL

| 环境 | Base URL | 备注 |
|------|----------|------|
| `prod-global` | `https://api.justoneapi.com` | 默认 |
| `prod-cn` | `http://47.117.133.51:30015` | 中国大陆可选 |

## 认证方式

**所有请求必须通过 URL query 参数传递 token**（不是 Header）：

```
GET https://api.justoneapi.com/api/{path}?token=YOUR_TOKEN&...
```

## 核心 API 路径速查

### 小红书 (xiaohongshu)

```
GET /api/xiaohongshu/search-note/v3          # 笔记搜索 V3
GET /api/xiaohongshu/search-note/v2          # 笔记搜索 V2
GET /api/xiaohongshu/get-user/v3              # 用户资料 V3
GET /api/xiaohongshu/get-user/v4              # 用户资料 V4
GET /api/xiaohongshu/get-user-note-list/v4    # 用户发布笔记 V4
GET /api/xiaohongshu/get-note-detail/v2       # 笔记详情 V2
GET /api/xiaohongshu/get-note-comment/v2      # 笔记评论 V2
GET /api/xiaohongshu/search-user/v2          # 用户搜索 V2
GET /api/xiaohongshu/share-url-transfer/v1    # 分享链接解析
GET /api/xiaohongshu/search-recommend/v1      # 关键词建议
```

### 抖音 (douyin)

```
GET /api/douyin/search-video/v4              # 视频搜索 V4 ← 主力接口
GET /api/douyin/search-user/v2               # 用户搜索 V2 ← 主力接口
GET /api/douyin/get-video-detail/v2          # 视频详情 V2（参数用 awemeId）
GET /api/douyin/get-video-comment/v1         # 视频评论 V1
```

> ⚠️ **抖音接口实测（2026-05-18）**：`get-user/v3` 和 `get-user-video/v3` 返回 500（路径不存在）。用户视频列表无直接接口，需通过视频搜索关键词绕过。`get-video-detail/v2` 参数名不是 `videoId`，而是 `awemeId`。

### 微博 (weibo)

```
GET /api/weibo/hot-search/v1                  # 微博热搜 ← 可用
GET /api/weibo/search/v2                      # 关键词搜索 V2（不稳定，返回500）
GET /api/weibo/get-user/v3                    # 用户资料 V3
GET /api/weibo/post-detail/v1                 # 帖子详情
```

> ⚠️ **微博搜索接口不稳定**，`search/v2` 实测返回 500，建议用热搜接口代替。

### 哔哩哔哩 (bilibili)

```
GET /api/bilibili/search-video/v2             # 视频搜索 V2（多字符中文关键词返回空）
GET /api/bilibili/video-detail/v2             # 视频详情 V2
GET /api/bilibili/get-user/v2                 # 用户资料 V2
GET /api/bilibili/user-published-video/v2     # 用户发布视频 V2
```

> ⚠️ **B站多字符中文关键词返回空**（如「十堰黑客松」搜不到，单字如「AI」正常）。疑似服务端 URL 编码问题。当前无替代接口，只能绕道用小红书/抖音搜索结果作参考。

### 微信 (weixin)

> ⚠️ **微信接口全部返回 500**，不支持公众号/文章查询。

### Twitter / X

> ⚠️ **Just One API 没有 Twitter 接口**，如需查询请用 `x-twitter-automation` skill（需要 cookies 认证）。

### 跨平台搜索

```
```
GET /api/search/v1                             # 跨平台搜索（微博、小红书、抖音等）
```

## curl 调用示例

```bash
# 注意：所有 curl 命令必须加 --noproxy '*' 跳过代理

# 小红书笔记搜索
curl -s --noproxy '*' \
  "https://api.justoneapi.com/api/xiaohongshu/search-note/v3?token=YOUR_TOKEN&keyword=AI&page=1&pageSize=10"

# 微博热搜
curl -s --noproxy '*' \
  "https://api.justoneapi.com/api/weibo/hot-search/v1?token=YOUR_TOKEN"

# 抖音视频搜索
curl -s --noproxy '*' \
  "https://api.justoneapi.com/api/douyin/search-video/v4?token=YOUR_TOKEN&keyword=AI&page=1&pageSize=10"

# 跨平台搜索
curl -s --noproxy '*' \
  "https://api.justoneapi.com/api/search/v1?token=YOUR_TOKEN&keyword=AI&pageSize=5"

# 中国节点（如需要）
curl -s --noproxy '*' \
  "http://47.117.133.51:30015/api/xiaohongshu/search-note/v3?token=YOUR_TOKEN&keyword=AI"
```

## 响应格式

```json
{
  "code": 0,
  "data": { ... },
  "message": "success",
  "recordTime": "2026-05-18T05:30:00.000Z"
}
```

### 业务码说明

| code | 含义 | 是否计费 |
|------|------|---------|
| 0 | 成功 | 是 |
| 100 | Token 无效或未激活 | 否 |
| 301 | 采集失败，请重试 | 否 |
| 302 | 超出速率限制 | 否 |
| 303 | 超出每日配额 | 否 |
| 400 | 参数错误 | 否 |
| 500 | 内部服务器错误 / 路径不存在 | 否 |
| 600 | 权限不足 | 否 |
| 601 | 余额不足 | 否 |

## Python SDK（推荐方式）

pip 安装（加 `--break-system-packages` 绕过系统限制）：

```bash
pip install justoneapi --break-system-packages
```

**⚠️ SDK 安装路径陷阱（2026-05-18 新发现）：**

SDK 安装到 `/home/ubuntu/.local/lib/python3.12/site-packages/`，但 Hermes Agent 的 `execute_code` Python 环境**不自动包含这个路径**。必须手动插入：

```python
import subprocess
r = subprocess.run([
    'python3.12', '-c', '''
import sys
sys.path.insert(0, "/home/ubuntu/.local/lib/python3.12/site-packages")
from justoneapi import JustOneAPIClient
client = JustOneAPIClient(token="YOUR_TOKEN")
...
'''
], ...)
```

**⚠️ httpx SSL 错误陷阱（2026-05-18 新发现）：**

`execute_code` 中的 SDK（httpx）走系统代理，导致 SSL EOF 错误。**`terminal` 工具用 curl + `--noproxy '*'` 绕过代理更可靠。** 推荐优先用 curl 直接调 REST API，不走 SDK：

```bash
# ✅ 可靠：curl 直接调 REST API
curl -s --noproxy '*' \
  "https://api.justoneapi.com/api/douyin/search-video/v4?keyword=关键词&page=1&token=TOKEN"

# ⚠️ SDK（httpx）会走代理触发 SSL 错误
# 错误信息：httpx.ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING]
```

**SDK vs curl 对照：**

| 平台 | SDK 方法 | curl 路径 | 返回结构 |
|------|---------|----------|---------|
| 小红书笔记搜索 | `search_note_v2()` | `/api/xiaohongshu/search-note/v2` | `data.items[].note.liked_count` |
| 抖音视频搜索 | `search_video_v4()` | `/api/douyin/search-video/v4` | `data.business_data[].data.aweme_info.statistics.digg_count` |
| B站视频搜索 | `search_video_v2()` | `/api/bilibili/search-video/v2` | `data.business_data[]`（中文关键词常返回空） |
| 微博热搜 | `hot_search_v1()` | `/api/weibo/hot-search/v1` | `data.business_data` |

> ⚠️ **SDK 方法名 ≠ curl 路径**。例如小红书 curl 路径是 `/api/xiaohongshu/search-note/v2`，但 SDK 方法是 `search_note_v2()`。不要混用，以 SDK 方法签名为准。

SDK 初始化和调用示例（直接 curl 更可靠，但 SDK 数据结构更完整）：

```python
# 小红书笔记搜索 → 返回 data.items（不是 business_data.items！）
resp = client.xiaohongshu.search_note_v2(keyword="关键词", page=1, sort="popularity_descending")
items = resp.data.get("items", []) if resp.data else []
for n in items[:5]:
    note = n.get("note", {})
    like = note.get("liked_count", 0)
    coll = note.get("collected_count", 0)
    print(f"赞{like} 藏{coll} | {note.get('desc','')[:60]}")

# 抖音视频搜索 → 返回 data.business_data[].data.aweme_info
resp2 = client.douyin.search_video_v4(keyword="关键词")
for item in resp2.data.get("business_data", []):
    info = item.get("data", {}).get("aweme_info", {})
    like = info.get("statistics", {}).get("digg_count", 0)
    desc = info.get("desc", "")[:60]
    print(f"赞{like} | {desc}")
```
> ⚠️ **SDK 方法名 ≠ curl 路径**。例如小红书 curl 路径是 `/api/xiaohongshu/search-note/v2`，但 SDK 方法是 `search_note_v2()`。不要混用，以 SDK 方法签名为准。

## 直接 curl 调用（如 SDK 不可用）

```python
import requests

def call_justoneapi(token: str, path: str, params: dict) -> dict:
    base_url = "https://api.justoneapi.com"
    all_params = {"token": token, **params}
    resp = requests.get(
        f"{base_url}{path}",
        params=all_params,
        timeout=60,
        proxies={"http": None, "https": None},
        trust_env=False
    )
    return resp.json()

result = call_justoneapi(
    token="YOUR_TOKEN",
    path="/api/xiaohongshu/search-note/v2",
    params={"keyword": "AI", "page": 1, "pageSize": 10}
)
```

## 踩坑记录

1. **curl 必须加 `--noproxy '*'`**，否则请求走代理导致超时或响应错误
2. **Python 跳过代理写法不同**：Python `requests` 不认 curl 的 `--noproxy`，需显式传 `proxies={"http": None, "https": None}, trust_env=False`
3. **Token 必须放 URL query 参数**，不是 Header（`Authorization: Bearer` 无效）
4. **路径格式是 `/api/{platform}/{operation}/v{ver}`**，不是 `/api/{full-path}`（如 `/api/xiaohongshu/search-note/v3`）
5. **pip 安装不上**（系统限制），推荐直接用 `requests` 调用 API
6. **code=301 FAILED, RETRY** 表示目标平台采集暂时失败，重试可能成功
7. **code=100 TOKEN INVALID/UNACTIVATE** 表示 Token 无效，需登录控制台激活
8. **小红书 userId 是内部ID（24位十六进制）**，不是纯数字 red_id，直接用会报错 `param userId not right`，需先通过 `search-user/v2` 查到内部 userId 再用
9. **抖音 `get-user/v3` 和 `get-user-video/v3` 返回 500**（路径不存在，无替代接口，需用视频搜索关键词绕过）
10. **抖音 `get-video-detail/v2` 参数名是 `awemeId`**，不是 `videoId`
11. **小红书 `get-user-note-list/v4` 响应慢**，需加 `--max-time 20`，超过10条容易超时
12. **小红书笔记字段 `likes` 和 `collected_count` 是直接字段**，非嵌套在 `interactInfo` 下；`interactInfo` 里有冗余副本，取值时应优先取直接字段

## 状态检查命令

```bash
# 测试任意接口（返回 code=100 说明 token 无效，返回其他说明连通）
curl -s --noproxy '*' "https://api.justoneapi.com/api/health?token=YOUR_TOKEN"
```

## 平台能力速查表（实测结论）

| 平台 | 搜索 | 用户资料 | 用户内容列表 | 详情 | 评论 | 备注 |
|------|------|---------|------------|------|------|------|
| 小红书 | ✅ search-note | ✅ get-user | ✅ get-user-note-list | ✅ get-note-detail | ✅ get-note-comment | 主力平台 |
| 抖音 | ✅ search-video | ❌ 路径不存在 | ❌ 路径不存在 | ⚠️ 参数用 awemeId | ✅ get-video-comment | 第二强 |
| 微博 | ⚠️ 仅热搜 | ❌ 未验证 | ❌ 未验证 | ❌ 未验证 | ❌ 未验证 | search不稳定 |
| B站 | ⚠️ 仅英文 | ❌ 未验证 | ❌ 未验证 | ❌ 未验证 | ❌ 未验证 | 中文关键词返回空 |
| 微信 | ❌ 全部500 | ❌ | ❌ | ❌ | ❌ | 不支持 |
| Twitter/X | ❌ 无搜索接口 | ✅ get_user_posts_v1 | ❌ | ❌ | ❌ | SDK 有 get_user_posts_v1，curl 接口不存在 |

## 相关文件

- `references/shiyi-hackathon-impact-20260518.md` — 十堰黑客松全网声量实测数据
- `references/xiaohongshu-account-analysis-20260518.md` — 小红书账号94348811612分析（2026-05-18）
- `references/xiaohongshu-account-analysis-20260522.md` — 小红书账号94348811612最新数据（含限流分析、封面图评估、GitHub链接规范）
- `references/xiaohongshu-userid-vs-redid.md` — 小红书 red_id vs userId 解析及短链接处理