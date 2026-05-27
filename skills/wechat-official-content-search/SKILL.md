---
name: wechat-official-justone-search
version: 1.1.0
description: 使用 Just One API 获取微信公众号公开内容，包括关键词搜索、账号发文、文章详情、文章互动指标和文章评论。适用于公众号内容发现、活动线索整理、媒体监测、文章研究和选题分析；内置正文读取失败与模型幻读防护规则。
---

# 微信公众号内容获取 Skill

## Overview

本 Skill 用于通过 Just One API 获取微信公众号公开内容，并把接口返回结果整理成适合内容发现、活动线索整理、媒体监测、文章研究和选题分析的结构化信息。

本 Skill 使用 Python 脚本 `scripts/wechat_official_client.py` 调用 Just One API。

默认接入地址：

```text
https://api.justoneapi.com
```

中国大陆可选接入地址：

```text
http://47.117.133.51:30015
```

认证方式：在 URL query 中携带 `token`。

Token 必须从环境变量 `JUSTONE_API_TOKEN` 读取，禁止写入 Skill 文档、代码、日志或最终回答。

可选环境变量：

```bash
export JUSTONE_API_TOKEN="你的 token"
export JUSTONE_API_BASE_URL="https://api.justoneapi.com"
```

---

## When to use this skill

当用户需要获取、搜索、整理或分析微信公众号公开内容时，使用本 Skill。

典型触发语：

- “帮我搜一下公众号里关于……的文章”
- “查一下微信公众号最近有没有……活动”
- “获取这个公众号最近发了什么”
- “获取这篇微信文章详情”
- “获取这篇公众号文章评论”
- “看看这篇文章的点赞/分享/评论指标”
- “帮我整理公众号里关于黑客松/AI Agent/活动报名的信息”
- “根据公众号搜索结果整理活动线索”
- “分析公众号文章选题/标题/传播点”

---

## What this skill can do

可以做：

- 关键词搜索微信公众号内容
- 搜索公众号账号、文章、视频号等结果类型
- 按默认、最新、热门排序搜索
- 获取微信公众号用户发布帖子
- 获取微信公众号文章详情
- 获取微信公众号文章互动指标
- 获取微信公众号文章评论
- 基于接口返回字段整理候选文章、活动线索、账号发文时间线
- 基于完整正文进行文章摘要、结构拆解、选题分析
- 基于评论进行用户反馈和需求分析

---

## What this skill must not do

禁止：

- 不获取私密内容、未公开内容、登录态内容、后台数据
- 不绕过登录、验证码、风控、权限限制或平台安全机制
- 不刷阅读、点赞、分享、评论、在看
- 不伪造微信公众号数据
- 不编造接口没有返回的信息
- 不把搜索摘要当作完整正文
- 不把样例数据当真实数据
- 不输出、保存、打印或泄露 Token
- 不声称搜索结果覆盖全网或微信公众号全量内容
- 不在样本不足时下确定性结论
- 不根据单次接口失败武断判断接口永久不可用
- 不在 `article_detail` 失败时生成完整文章摘要、完整赛程、报名方式、地点、奖项或主办方等正文级信息

遇到违规或数据不足请求时，应拒绝违规部分，并提供合规替代方案，例如：公开搜索结果整理、候选线索列表、缺失字段标注、等待正文接口恢复、让用户提供文章截图或原文。

---

## Inputs

用户可能提供以下输入：

### keyword

用于关键词搜索公众号内容。

示例：

```text
AI Agent
黑客松
活动报名
创业比赛
十堰黑客松
```

### wxid

用于获取某个微信公众号的公开发文列表。

示例：

```text
rmrbwx
```

### articleUrl

用于获取文章详情、互动指标、评论。

示例：

```text
https://mp.weixin.qq.com/s/xxxx
```

---

## Actions

| action | 用途 | 对应接口 |
|---|---|---|
| `search` | 关键词搜索 | `GET /api/weixin/search/v1` |
| `user_posts` | 获取公众号用户发布帖子 | `GET /api/weixin/get-user-post/v1` |
| `article_detail` | 获取文章详情正文 | `GET /api/weixin/get-article-detail/v1` |
| `article_feedback` | 获取文章互动指标 | `GET /api/weixin/get-article-feedback/v1` |
| `article_comments` | 获取文章评论 | `GET /api/weixin/get-article-comment/v1` |

---

## Workflow

### Step 1: 判断用户意图

| 用户需求 | 优先 action |
|---|---|
| 搜公众号文章 | `search --search-type _2` |
| 搜公众号账号 | `search --search-type _1` |
| 搜全部微信结果 | `search --search-type _0` |
| 搜最新文章 | `search --search-type _2 --sort-type _2` |
| 搜热门文章 | `search --search-type _2 --sort-type _4` |
| 看公众号发文时间线 | `user_posts --wxid <wxid>` |
| 获取文章正文 | `article_detail --article-url <url>` |
| 获取文章互动指标 | `article_feedback --article-url <url>` |
| 获取文章评论 | `article_comments --article-url <url>` |
| 整理活动线索 | 优先 `search`，正文可用时再 `article_detail` |

---

### Step 2: 执行 Python 脚本

调用格式：

```bash
python scripts/wechat_official_client.py <action> [参数]
```

示例：

```bash
python scripts/wechat_official_client.py search \
  --keyword "AI Agent" \
  --offset 0 \
  --search-type _2 \
  --sort-type _2
```

---

### Step 3: 检查返回结果

必须同时检查：

- HTTP 状态码
- 返回体是否为 JSON
- `code`
- `data`
- `message` / `msg` / `error`
- `is_collect_failed`
- `failure_type`

业务成功只以 `code == 0` 为准。

如果 `code != 0`：

- 不生成事实结论
- 不生成正文摘要
- 不生成趋势判断
- 不生成活动详情确认
- 只能说明失败原因和下一步建议

---

### 常见失败模式

| 场景 | 特征 | 处理 |
|---|---|---|
| `article_detail` 返回 `COLLECT FAILED` | code=301，多公众号同步发布的预告文章容易被拦截 | 改用搜索结果摘要（`desc`字段），不强行读取正文；或换其他公众号账号发布的同一活动文章重试 |
| 搜索返回空但实际有结果 | 关键词含"上海 6月"等复合词时源站返回异常 | 拆词搜索，分两次调用 |
| Token无效（code=100） | 环境变量未设置或已过期 | 确认 `JUSTONE_API_TOKEN` 已写入当前 session 环境变量 |

### 自动重试策略

- `article_detail` 失败时，不立即重试同一 URL，先用同一活动不同公众号文章兜底
- 搜索报 `COLLECT FAILED` 时，换 `sortType`（默认→最新→热门）重试
- 搜索报 `TOKEN INVALID` 时，检查 token 是否写入环境变量，不重复调用

### 输出格式约定

公众号搜索返回结果后，整理为：

```text
## 结论
[一句话概括]

## 样本情况
本次共 N 条结果，去重后 M 条。

## 事实数据
1. 标题 | 来源公众号 | 发布时间
   摘要…

## 样本观察
[活动发布时间线/集中度/信息可信度]

## 数据限制
本结果仅基于公众号搜索，不保证覆盖所有平台。
```

## Anti-hallucination rules

这是本 Skill 的核心规则，必须优先执行。

### 总规则

1. 只基于接口返回的 `data` 回答。
2. 字段不存在、为空、无法解析时，统一写“未获取到”或“接口未返回”。
3. 不得根据标题、摘要、常识、经验或相似活动补全事实。
4. 不得把搜索摘要包装成完整正文。
5. 不得把候选线索写成“已确认活动详情”。
6. 事实数据、样本观察、运营建议必须分开。
7. 样本不足时，必须写“样本不足，不能代表公众号整体或全网趋势”。
8. 接口失败时，不得继续生成分析结论。
9. 所有推测性内容必须改写为“待确认项”，不能写成事实。

### 正文读取失败规则

当 `article_detail` 返回以下任意情况时，视为正文读取失败：

- `code != 0`
- `message`、`msg`、`error` 中包含 `COLLECT FAILED`
- `data` 为空
- `data` 中没有正文内容字段
- HTTP 超时或请求失败

正文读取失败时：

1. 不得生成完整文章摘要。
2. 不得补全正文中可能存在的报名链接、赛程、地点、奖项、主办方、报名截止时间等信息。
3. 只能使用搜索接口实际返回的字段，例如标题、摘要、发布时间、公众号名称、文章链接。
4. 对缺失字段统一标注为“未获取到”。
5. 可以做“候选活动线索列表”，但不能写成“已确认活动详情”。
6. 如需完整详情，应提示用户提供文章链接、截图、原文内容，或等待正文接口恢复。
7. 不得使用“大概率”“应该是”“交叉推断”等方式把不完整信息包装成事实。

推荐提示：

```text
⚠️ 信息来源受限：公众号搜索接口可用，但文章正文读取 article_detail 返回 COLLECT FAILED 或未返回正文，暂时无法获取完整正文、详细赛程和报名信息。以下内容仅基于公众号搜索结果中的标题、摘要、发布时间等字段整理；凡接口未返回的信息，一律标记为“未获取到”，不得补全或推断为确定事实。
```

---

## Default behavior

当用户没有指定搜索类型：

- 找文章：`searchType=_2`
- 找公众号账号：`searchType=_1`
- 不确定：`searchType=_0`

当用户没有指定排序：

- 普通内容发现：`sortType=_0`
- 最近/最新：`sortType=_2`
- 热门/爆款：`sortType=_4`

分页规则：

- `offset` 默认 `0`
- 下一页通常 `offset += 20`
- 输出时说明本次样本只来自当前 offset 返回结果

---

## Error handling

Just One API 业务码处理：

| code | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | 只基于 `data` 输出 |
| 100 | Token 无效或失效 | 检查 `JUSTONE_API_TOKEN` |
| 301 | 采集失败 | 可有限重试；若为正文失败，按正文读取失败规则处理 |
| 302 | 超出速率限制 | 等待后重试 |
| 303 | 超出每日配额 | 停止请求，提示配额不足 |
| 400 | 参数错误 | 检查参数，不重试 |
| 500 | 内部服务器错误 | 稍后重试 |
| 600 | 权限不足 | 检查接口权限 |
| 601 | 余额不足 | 提醒充值 |

失败输出模板：

```text
本次请求失败，未获取到有效数据。

接口：{action}
原因：{message}
业务码：{code}
处理：不会基于失败结果编造文章内容或活动详情。
```

---

## Content index

### 1. 关键词搜索

Action：

```bash
search
```

接口：

```http
GET /api/weixin/search/v1
```

参数：

```text
keyword: 必填，搜索关键词
offset: 可选，默认 0，每次增加 20
searchType: 可选，默认 _0
sortType: 可选，默认 _0
```

searchType：

```text
_0: 全部
_1: 微信公众号
_2: 文章
_7: 微信视频号
_262208: 微信小程序
_384: 表情
_16777728: 百科
_9: 直播
_1024: 图书
_512: 音乐
_16384: 新闻
_8192: 微信指数
_8: 朋友圈
```

sortType：

```text
_0: 默认
_2: 最新
_4: 热门
```

示例：

```bash
python scripts/wechat_official_client.py search \
  --keyword "黑客松" \
  --offset 0 \
  --search-type _2 \
  --sort-type _2
```

---

### 2. 获取公众号发文

Action：

```bash
user_posts
```

接口：

```http
GET /api/weixin/get-user-post/v1
```

参数：

```text
wxid: 必填，微信公众号 ID
```

示例：

```bash
python scripts/wechat_official_client.py user_posts \
  --wxid "rmrbwx"
```

---

### 3. 获取文章详情

Action：

```bash
article_detail
```

接口：

```http
GET /api/weixin/get-article-detail/v1
```

参数：

```text
articleUrl: 必填，微信文章 URL
```

示例：

```bash
python scripts/wechat_official_client.py article_detail \
  --article-url "https://mp.weixin.qq.com/s/xxxx"
```

注意：如果该接口返回 `COLLECT FAILED`，必须执行“正文读取失败规则”。

---

### 4. 获取文章互动指标

Action：

```bash
article_feedback
```

接口：

```http
GET /api/weixin/get-article-feedback/v1
```

参数：

```text
articleUrl: 必填，微信文章 URL
```

示例：

```bash
python scripts/wechat_official_client.py article_feedback \
  --article-url "https://mp.weixin.qq.com/s/xxxx"
```

---

### 5. 获取文章评论

Action：

```bash
article_comments
```

接口：

```http
GET /api/weixin/get-article-comment/v1
```

参数：

```text
articleUrl: 必填，微信文章 URL
```

示例：

```bash
python scripts/wechat_official_client.py article_comments \
  --article-url "https://mp.weixin.qq.com/s/xxxx"
```

---

## Output rules

### 搜索结果输出模板

```text
## 数据状态

公众号搜索：可用
文章正文读取：未调用 / 成功 / 失败
可用字段：标题、摘要、发布时间、公众号名称、文章链接
不可确认字段：详细赛程、报名方式、地点、奖项、完整活动规则

## 当前结果

以下内容仅基于本次接口返回数据整理，不代表完整活动详情。

| 标题 | 公众号 | 发布时间 | 摘要信息 | 详情状态 |
|---|---|---|---|---|
| ... | ... | ... | ... | 正文未获取到 |

## 待确认项

- 报名链接：未获取到
- 详细赛程：未获取到
- 活动地点：未获取到
- 主办方：未获取到
- 奖项设置：未获取到

## 数据限制

本结果仅基于当前接口返回样本；正文未获取到时，不能确认完整详情。
```

### 文章详情成功输出模板

```text
## 文章信息

标题：...
公众号：...
发布时间：...
文章链接：...

## 正文摘要

...

## 关键信息

- 报名方式：...
- 时间安排：...
- 地点：...
- 主办方：...
- 奖项：...

## 数据限制

以上信息仅基于 article_detail 接口实际返回字段整理。
```

---

## Quality checklist

最终回答前必须检查：

- 是否使用了正确 action
- 是否从环境变量读取 Token
- 是否检查了 `code == 0`
- 是否识别 `COLLECT FAILED`
- 是否避免把搜索摘要当正文
- 是否把缺失字段标注为“未获取到”
- 是否区分事实、样本观察和建议
- 是否避免编造报名链接、赛程、地点、奖项、主办方
- 是否说明数据限制
