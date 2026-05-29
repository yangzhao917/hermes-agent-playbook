---
name: xiaohongshu-justone-fallback
summary: 使用 Just One API 获取小红书站内公开信息，作为 Rnote 不可用时的备用数据源。支持笔记搜索、用户搜索、笔记详情、评论、评论回复、用户主页笔记、分享链接解析和关键词建议；内置反幻读规则，禁止基于缺失字段或失败响应编造结论。
description: 当 Rnote 小红书接口不可用、超时、余额不足、限流、返回空数据或需要第二数据源交叉验证时，使用 Just One API 获取小红书公开信息，并将结果整理为选题、账号分析、竞品调研、评论区需求分析和内容复盘所需的结构化信息。
---

# 小红书 Just One API 备用 Skill

## 1. 定位

本 Skill 是 `xiaohongshu-info-search` 的备用数据源。默认优先使用 Rnote；当 Rnote 不可用、失败、超时、限流、返回空数据，或用户明确要求使用 Just One API 时，切换到本 Skill。

本 Skill 只获取小红书站内公开信息，不处理私密内容、不绕过登录/风控、不伪造数据。

## 2. 触发条件

满足以下任一情况时使用本 Skill：

- Rnote 接口失败、超时、限流、余额不足或返回空数据
- 用户说“换备用接口 / 用 Just One API / rnote 不可用 / 用另一个源查”
- 需要对 Rnote 返回结果做第二数据源验证
- 需要解析小红书分享链接获得 noteId
- 需要关键词建议扩展搜索词

典型请求：

- “Rnote 不行了，用备用接口搜小红书”
- “用 Just One API 查一下这个小红书笔记”
- “解析这个小红书链接，然后拉详情和评论”
- “用备用接口搜 AI Agent 求职的小红书内容”
- “帮我查这个账号发过什么”

## 3. 能力边界

可以做：

- 搜索小红书笔记
- 搜索小红书用户
- 获取笔记详情
- 获取笔记评论
- 获取评论回复
- 获取用户公开资料
- 获取用户公开发布笔记
- 解析小红书分享链接
- 获取关键词建议
- 对返回数据做摘要、分类、选题提炼、账号分析、评论区需求分析

不可以做：

- 不获取私信、私密账号、非公开收藏、非公开内容
- 不绕过登录、验证码、风控、权限限制
- 不刷赞、刷收藏、刷评论、刷粉
- 不批量骚扰用户
- 不伪造小红书数据
- 不把样例数据当真实数据
- 不输出、保存或泄露 token
- 不声称数据覆盖小红书全站
- 不根据单次接口结果武断判断限流、封号、违规

## 4. 环境变量

必须配置：

```bash
export JUSTONE_API_TOKEN="你的 Just One API token"
```

可选配置：

```bash
export JUSTONE_BASE_URL="https://api.justoneapi.com"
```

中国大陆服务器可按需使用：

```bash
export JUSTONE_BASE_URL="http://47.117.133.51:30015"
```

注意：Just One API 的认证方式是把 `token` 放在 URL query 参数里。脚本必须自动注入 token，日志和用户输出中不得展示 token。

## 5. 工作流

### Step 1：判断是否需要切换

优先使用 Rnote；以下情况切换本 Skill：

- Rnote HTTP 非 2xx
- Rnote `success != true`
- Rnote 超时
- Rnote 429 / 5xx
- Rnote 返回空 `data`
- 用户明确要求使用 Just One API

### Step 2：选择 action

| 用户需求 | action |
|---|---|
| 搜关键词笔记 | `search_notes` |
| 搜热门笔记 | `search_notes --sort popularity_descending` |
| 搜最近笔记 | `search_notes --sort time_descending` |
| 搜评论多的笔记 | `search_notes --sort comment_descending` |
| 搜收藏多的笔记 | `search_notes --sort collect_descending` |
| 搜用户 | `search_users` |
| 获取笔记详情 | `note_detail` |
| 获取可下载视频信息 | `note_detail_v5` |
| 获取评论 | `note_comments` |
| 获取评论回复 | `comment_replies` |
| 获取用户资料 | `user_profile` |
| 获取用户发布笔记 | `user_notes` |
| 解析分享链接 | `resolve_share` |
| 获取关键词建议 | `keyword_suggestions` |

### Step 3：执行脚本

```bash
python scripts/justone_client.py <action> [参数]
```

### Step 4：检查响应

必须同时检查：

- HTTP 状态码
- 返回体是否为 JSON
- `code == 0`
- `data` 是否存在且非空
- `message` 是否有错误说明

只有 `code == 0` 时才允许基于 `data` 做结论。

### Step 5：输出

不要直接把完整 JSON 扔给用户。优先整理为：

```text
## 结论
...

## 样本情况
本次获取到 ... 条结果。

## 代表内容
1. ...
2. ...
3. ...

## 观察到的趋势
...

## 可用选题
...

## 数据限制
本结果仅基于 Just One API 本次返回数据，不代表小红书全站完整情况。
```

## 6. 反幻读规则

必须遵守：

1. 只允许基于接口返回的 `data` 回答。
2. 字段不存在时，写“接口未返回”，不要猜。
3. `code != 0` 时，不得生成内容分析、趋势判断、选题建议。
4. 结果为空时，写“本次未获取到有效数据”，不要编造样本。
5. 不得把字段名推测成真实含义，除非字段内容明确。
6. 不得根据 1 条或极少样本代表全站趋势。
7. 必须区分“接口返回事实”“样本观察”“运营建议”。
8. 建议类内容必须标注为“基于样本的建议”，不能说成平台事实。
9. 多源切换时必须说明来源是 Just One API，而不是 Rnote。
10. 对于互动数、发布时间、作者信息，接口没有返回就不要补。

推荐输出分层：

```text
【接口返回事实】只写 data 中明确存在的信息。
【样本观察】只基于本次样本做弱结论。
【运营建议】基于样本观察给建议，不假装是平台规则。
【数据限制】说明样本来源、数量和不完整性。
```

## 7. 错误处理

Just One API 使用 `code` 字段判断业务结果：

| code | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | 可基于 data 输出 |
| 100 | Token 无效或已失效 | 检查 `JUSTONE_API_TOKEN` |
| 301 | 采集失败 | 可重试 |
| 302 | 超出速率限制 | 等待后重试 |
| 303 | 超出每日配额 | 停止请求，提示配额不足 |
| 400 | 参数错误 | 检查参数，不重试 |
| 500 | 内部服务器错误 | 稍后重试 |
| 600 | 权限不足 | 检查账号权限 |
| 601 | 余额不足 | 提示充值 |

失败时输出：

```text
本次 Just One API 请求失败，未获取到有效数据。
原因：{message 或 error}
code：{code}
我不会基于失败结果编造内容。
```

## 8. 内容索引与速查

### 搜索笔记

```bash
python scripts/justone_client.py search_notes --keyword "AI Agent 求职" --page 1 --sort general --note-type _0
```

排序：`general`、`popularity_descending`、`time_descending`、`comment_descending`、`collect_descending`。

笔记类型：`_0` 通用、`_1` 视频、`_2` 普通。

### 搜索用户

```bash
python scripts/justone_client.py search_users --keyword "AI Agent" --page 1
```

### 获取笔记详情

```bash
python scripts/justone_client.py note_detail --note-id NOTE_ID
```

### 获取视频/媒体详情

```bash
python scripts/justone_client.py note_detail_v5 --note-id NOTE_ID
```

注意：V5 文档提示不包含互动指标，需要互动指标时优先用 `note_detail`。

### 获取评论

```bash
python scripts/justone_client.py note_comments --note-id NOTE_ID --sort latest
```

### 获取评论回复

```bash
python scripts/justone_client.py comment_replies --note-id NOTE_ID --comment-id COMMENT_ID
```

### 获取用户资料

```bash
python scripts/justone_client.py user_profile --user-id USER_ID
```

### 获取用户发布笔记

```bash
python scripts/justone_client.py user_notes --user-id USER_ID
```

### 解析分享链接

```bash
python scripts/justone_client.py resolve_share --share-url "https://xhslink.com/..."
```

### 获取关键词建议

```bash
python scripts/justone_client.py keyword_suggestions --keyword "AI Agent"
```

## 9. 默认策略

- 普通调研：`search_notes --sort general --note-type _0`
- 最近内容：`search_notes --sort time_descending`
- 爆款参考：`search_notes --sort popularity_descending`
- 评论区需求：先 `note_detail`，再 `note_comments`
- 链接输入：先 `resolve_share`，再根据返回的 noteId 获取详情/评论
- 账号分析：先 `user_profile`，再 `user_notes`
- 选题扩展：先 `keyword_suggestions`，再 `search_notes`

## 10. 完成前检查

回答用户前检查：

- 是否确认使用的是 Just One API 备用源
- 是否检查 `code == 0`
- 是否只基于 `data` 输出
- 是否避免泄露 token
- 是否避免编造缺失字段
- 是否说明样本限制
- 是否区分事实、观察、建议
- 是否给出可执行运营建议
