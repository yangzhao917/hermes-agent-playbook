---
name: wechat-official-justone-skill
version: 1.2.2
description: 使用 Just One API 获取微信公众号公开内容，包括关键词搜索、账号发文、文章详情、文章互动指标和文章评论。当前搜索正常；文章正文读取存在限流/COLLECT FAILED 风险，内置限速、缓存、降级和防幻读规则。
---

# 微信公众号内容获取 Skill

## 当前状态

Skill：wechat-official-justone-skill  
版本：v1.2.4  
可用性：✅ 公众号搜索正常；⚠️ 文章正文读取存在限流 / COLLECT FAILED 风险  
默认策略：搜索优先，正文按需读取；正文失败时自动降级为“候选线索模式”。

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

认证方式：在 URL query 中携带 `token`。Token 只允许从环境变量 `JUSTONE_API_TOKEN` 读取。禁止提供默认 Token，禁止把真实 Token 写入 Skill 文档、代码仓库、日志或最终回答。

环境变量说明：除 Token 外，以下运行参数已在脚本中内置默认值，不配置也能使用。需要覆盖默认策略时再设置：

```bash
export JUSTONE_API_TOKEN="你的 token"
# 可选：本机/私有部署兜底，JUSTONE_API_TOKEN 未配置时读取；不要提交真实 token
export JUSTONE_API_BASE_URL="https://api.justoneapi.com"
export JUSTONE_TIMEOUT="75"
export JUSTONE_MAX_RETRIES="1"
export JUSTONE_DETAIL_MIN_INTERVAL_SECONDS="8"
export JUSTONE_DETAIL_CACHE_TTL_SECONDS="604800"
export JUSTONE_SEARCH_CACHE_TTL_SECONDS="21600"
export JUSTONE_CACHE_DIR=".cache/justone_wechat"
```

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

## What this skill must not do

禁止：

- 不获取私密内容、未公开内容、登录态内容、后台数据
- 不绕过登录、验证码、风控、权限限制或平台安全机制
- 不通过高并发、代理池、频繁重试等方式规避限流
- 不伪造公众号文章、评论、互动数或正文内容
- 不编造接口没有返回的信息
- 不把搜索摘要当作完整正文
- 不把候选线索写成已确认活动详情
- 不输出、保存、打印或泄露 token
- 不声称数据覆盖微信公众号全站
- 不在样本不足时下确定结论

## Core strategy for正文读取限流

文章正文读取限流无法在 Skill 内彻底“消除”，只能通过更稳的调用策略降低失败率，并在失败时防止模型幻读。

### 解决策略

1. 搜索优先：先用 `search` 获取候选文章，不要对每条搜索结果立刻读取正文。
2. 按需读取：只有用户明确需要正文、报名详情、赛程、地点、规则时，才调用 `article_detail`。
3. 串行读取：`article_detail` 默认单线程，不并发。
4. 限速读取：两次 `article_detail` 默认间隔不少于 8 秒，可通过 `JUSTONE_DETAIL_MIN_INTERVAL_SECONDS` 调整。
5. 成功缓存：正文读取成功后缓存 7 天，相同文章 URL 不重复采集。
6. URL 去重：自动清理微信文章 URL 的无关追踪参数，减少重复请求。
7. 少重试：`COLLECT FAILED` / `code=301` 不做连续强重试，直接降级，避免加剧限流。
8. 降级模式：正文失败时，只输出搜索结果层面的候选线索。

## Workflow

### Step 1：判断任务类型

| 用户需求 | 优先 action |
|---|---|
| 搜公众号文章 | `search --search-type _2` |
| 搜公众号账号 | `search --search-type _1` |
| 搜最近内容 | `search --sort-type _2` |
| 搜热门内容 | `search --sort-type _4` |
| 获取账号发文 | `user_posts` |
| 获取文章正文 | `article_detail` |
| 获取互动指标 | `article_feedback` |
| 获取评论 | `article_comments` |

### Step 2：优先搜索，不要批量读正文

示例：

```bash
python scripts/wechat_official_client.py search \
  --keyword "黑客松" \
  --offset 0 \
  --search-type _2 \
  --sort-type _2
```

搜索结果可用于整理：标题、摘要、公众号名称、发布时间、文章链接等候选线索。

### Step 3：只对关键候选文章读取正文

示例：

```bash
python scripts/wechat_official_client.py article_detail \
  --article-url "https://mp.weixin.qq.com/s/xxxx"
```

正文读取成功时，才允许做完整文章摘要、报名信息提取、赛程整理、地点/奖项/主办方提取。

### Step 4：正文失败自动降级

当 `article_detail` 返回以下任一情况时，必须进入候选线索模式：

- `COLLECT FAILED`
- `code=301`
- HTTP 429 / 5xx
- `data` 为空
- `data` 中没有正文内容字段
- `failure_type` 不为空
- `anti_hallucination.can_summarize_full_article=false`

## 候选线索模式规则

正文读取失败时：

1. 只能使用搜索接口实际返回的标题、摘要、公众号名称、发布时间、文章链接等字段。
2. 不得生成完整文章摘要。
3. 不得补全报名链接、赛程安排、活动地点、奖项、主办方、活动规则等正文信息。
4. 缺失字段统一标记为“未获取到”。
5. 搜索结果只能表述为“候选线索”，不能表述为“已确认活动详情”。
6. 输出时必须提示：公众号搜索正常，但正文读取受限。
7. 不得使用“交叉推断”“大概率”“应该是”等表达把缺失信息包装成事实。

## Error handling

业务成功必须以接口响应体 `code == 0` 为准；HTTP 200 不等于业务成功。

常见状态：

| 情况 | 处理 |
|---|---|
| `code=0` 且存在正文 | 可做正文摘要与信息提取 |
| `code=301` / `COLLECT FAILED` | 不连续重试，降级候选线索模式 |
| HTTP 429 | 认为限流，降级或稍后重试 |
| 请求超时 | 不生成正文结论 |
| `data` 为空 | 缺失字段标记“未获取到” |
| 正文缺失 | 不把摘要当正文 |

失败输出模板：

```text
⚠️ 信息来源受限：公众号搜索正常，但文章正文读取受限，当前无法获取完整正文。以下内容仅基于搜索结果中的标题、摘要、发布时间、公众号名称、文章链接整理；凡接口未返回的信息，一律标记为“未获取到”，不得补全或推断为确定事实。
```

## Output rules

输出必须遵守：

- 事实数据、样本观察、运营建议分开
- 只基于 `success=true` 且存在的 `data` 输出事实
- 字段不存在时写“未获取到”
- 搜索结果不能替代正文
- 正文失败时禁止生成文章摘要
- 样本不足时不得代表公众号整体趋势
- 接口失败时只说明失败原因和下一步建议

推荐输出结构：

```text
## 数据状态
公众号搜索：可用
文章正文读取：成功 / 失败 / 限流 / COLLECT FAILED
当前模式：完整详情模式 / 候选线索模式

## 结果
...

## 未获取到的信息
- 报名链接：未获取到
- 详细赛程：未获取到
- 活动地点：未获取到
- 奖项设置：未获取到
- 主办方：未获取到

## 数据限制
本结果仅基于本次接口返回数据，不代表微信公众号全量结果。
```

## Quality checklist

最终回答前检查：

- 是否先搜索再按需读取正文
- 是否避免批量并发调用 `article_detail`
- 是否检查了 `code == 0`
- 是否检查了 `anti_hallucination.can_summarize_full_article`
- 是否把正文失败结果降级为候选线索
- 是否避免根据标题/摘要补全正文级事实
- 是否标注“未获取到”和数据限制
