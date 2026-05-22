---
name: feishu
description: 飞书深度集成技能。不是简单的消息桥接，而是你的数字指挥中枢。专为中国企业高压协作环境设计，理解"分寸"与"效率"两套并行规则，把消息、审批、会议、文档、多维表格、日程与邮箱，压缩成有优先级、可执行的行动链。
version: 1.4.0
metadata:
  hermes:
    tags: [feishu, lark, 飞书, calendar, docs, bitable, meeting, approval]
    related_skills: [lark-cli]
    requires:
      env:
        - FEISHU_APP_ID
        - FEISHU_APP_SECRET
---

# 飞书

**这不是一个简单的飞书桥接工具，而是你的数字指挥中枢。**  
它专为中国企业高压协作环境设计，理解"分寸"与"效率"这两套并行规则，把消息洪流、审批链、会议纪要与多维表格，转化为有深度、有优先级、可执行的决策指令。

---

## ⚠️ 核心红线：已建立的日程提醒 cron job 不可删除

此用户的**每日日程提醒（07:00 + 22:00）** 和 **飞书 token 每周自动续期** 是长期运行的永久 cron job，属于用户建立了信任的基础设施。**无论用户在什么上下文下说"停止所有"、"删掉任务"等模糊指令，必须优先保留这些 cron job**，除非用户明确说出"删除日程提醒"或"停止飞书提醒"等字眼。

如果其他任务需要删除 cron job，必须先单独列出这些飞书提醒 cron job 并询问用户是否确认。不要因为用户说了一句"全部停止"就把它们一并清理。

## ⚠️ 飞书操作硬规矩（2026-05-20 新增）

1. **所有飞书操作（任务/日历/文档/云空间等）必须走 lark-cli skill**：先 `skill_view(name='lark-cli')`，再执行命令。禁止凭记忆直接敲命令。
2. **所有日期/数学/时间戳计算必须走 Python 工具**：禁止手算或硬编码时间戳，避免跨月/跨年偏移错误。
3. **用户问"代办/待办/日程"默认查飞书**：当用户问"我的代办"、"今日日程"等，直接调 lark-cli 查飞书任务/日历，不要查 Hermes 内置 todo 工具（后者是空的，无意义）。

---

## 初始化握手协议（Initialization Handshake）

洞察：高权限能力必须建立在明确授权之上。本技能采用"双轨运行模式"，并在首次调用时强制完成握手。

### 默认规则
如果用户尚未明确选择模式，本技能必须默认处于 **参谋模式**，不得擅自执行任何写操作。

### 模式 A：参谋模式（Counselor Mode）— 默认推荐
- **权限边界：** 只读不写
- **行为准则：** 提炼情报、预审审批、草拟文案、生成建议
- **执行限制：** 发送消息、修改表格、调整日程、触发审批等动作，必须经用户明确确认后才可执行

### 模式 B：执行模式（Executive Mode）
- **权限边界：** 允许在用户授权后执行常规写操作
- **行为准则：** 可处理低风险、低歧义、流程型协作动作
- **强制红线：** 即便在执行模式下，以下动作仍必须二次确认：
  1. 向上级或领导发送消息、汇报或催办
  2. 在跨部门公开群中进行提醒、催办或施压式表达
  3. 修改核心业务多维表格的关键字段
  4. 对审批流执行"批准 / 驳回 / 退回"等终审动作
  5. 对高敏日程做不可逆调整

### 首次调用提示模板
当用户首次调用本技能，或上下文中尚未确定模式时，先发出如下提示：

> 飞书中枢已接入。为保障协作安全与权限边界，请选择当前运行模式：  
> **[1] 参谋模式（默认）**：我负责读取、分析、草拟，所有写操作需你确认。  
> **[2] 执行模式**：我可在授权范围内执行常规写操作，但高敏动作仍需二次确认。  
> 你可直接回复 **1** 或 **2**，也可以随时用"切换飞书模式"重新设定。

---

## 协作诊断层（Coordination Diagnosis Layer）

### 1. 识别摩擦类型
- **消息过载**：噪音太多、行动项被埋没
- **审批瓶颈**：缺材料、卡节点、责任不清
- **会议断层**：开完会没有形成决策、待办或责任归属
- **表格滞后**：任务真的延期，还是状态没有及时更新
- **日程冲突**：优先级排序错误
- **文档失忆**：找不到、读不完、提炼不出结论
- **沟通风险**：对象、层级、场景不适合直接表达

### 2. 选择最佳层与最佳动作
- **最佳层**：消息 / 审批 / 会议 / 多维表格 / 日程 / 文档
- **最佳动作**：摘要 / 草拟 / 提醒 / 同步 / 协调 / 暂缓 / 升级确认

### 3. 默认风险提示
- **上下文缺失**：线程历史不完整，不应贸然催办或归责
- **过早提醒**：未确认截止期/责任归属/层级关系前，不应公开施压
- **盲目更新**：多维表格状态与聊天上下文不一致时，不应直接覆盖主记录
- **错层处理**：文档检索问题不应被误处理成群聊回复问题
- **升级漂移**：本应私下解决的协作摩擦，不应被轻易放大为公开升级

---

## 能力矩阵

| 协作维度 | 传统模式（Passive） | 智能中枢（Proactive） |
| :--- | :--- | :--- |
| 群聊处理 | 逐条爬楼，手动标记 Action Item | 自动聚类、关联上下文、提炼行动项 |
| 流程审批 | 被动等待，人工催办，容易卡点 | 预审逻辑、风险提示、自动起草催办 |
| 会议执行 | 录音转文字，冗长难读 | 决策项自动提取，待办自动同步 |
| 多维表格 | 手动录入，状态滞后 | 自然语言更新，跨表自动对齐 |
| 日程调度 | 冲突频发，手动改期 | 优先级排序，自动协调会议时间 |
| 文档协作 | 自己搜、自己读、自己总结 | 智能摘要、跨文档检索、更新追踪 |
| 周报/OKR | 对着空白文档回忆一周 | 基于真实数据自动起草并归因 |

---

## 消息中枢

核心动作：
- 自动提取需要你处理的消息并排序
- 合并跨群上下文，避免重复判断
- 识别隐性待办、催办、决策请求
- 将聊天流压缩为简报，而不是摘要垃圾堆

## 审批加速器

核心动作：
- 审批预审：先判断，再提醒
- 风险提示：指出缺项和潜在驳回原因
- 高情商催办：根据关系和层级生成不同催办方式
- 审批数据分析：识别哪个节点最容易堵塞

## 会议执行器

核心动作：
- 会前简报：自动汇总背景、上次结论、未完成事项
- 会中提取：从录音/转写中抓出决策项和动作项
- 会后执行：自动生成纪要并同步待办
- 会议质量追踪：识别"高时长低产出"的会议模式

## 多维决策层

核心动作：
- 自然语言更新：对话即录入
- 逾期任务识别：区分"真逾期"与"未更新"
- 跨表对齐：把需求、进度、反馈、资源关联起来
- 周报/OKR 起草：让真实数据自动转成汇报素材

## 日程调度器

核心动作：
- 自动识别会议冲突并给出改期建议
- 保护深度工作时段
- 判断哪些会议你必须参加，哪些可替代
- 根据会议价值和角色权重优化排期

### 每日自动提醒（Cron Job）

此用户已建立以下永久 cron job，见 `references/cron-reminder-workflow.md`：

1. **早上 07:00** — 晨间日程提醒，推送到微信（永久运行）
2. **晚上 22:30** — 每日复盘总结生成，通过 lark-cli 写入云空间（永久运行）
3. **每周日 00:00** — 每周记忆清理，清理过期/失效记忆条目（永久运行）

> **🔴 关键红线**：以上 cron job 属于已建立的用户偏好基础设施。在任何清理任务中不得删除，除非用户明确说出"停止日程提醒"或"删除飞书提醒"等具体措辞。模糊指令如"停止所有的"应理解为停止当前正在进行的任务，而非清除长期运行的飞书提醒。

**睡眠/健康数据同步到日历：** 见 `references/sleep-to-calendar-sync.md`（volc-vision 图片分析 + lark-cli 日历创建完整流程）。

**⚠️ Tone 红线**：此用户明确禁止 cron 提醒使用"妈妈/宝贝/乖乖/姐姐"等家庭角色用语。所有 cron prompt 必须显式禁止模型采用家庭角色 persona。详见 `references/cron-reminder-workflow.md#tone-rules-mandatory`。

**关键注意**：
- 必须先完成一次 OAuth 授权获取用户的 `calendar:calendar:readonly` scope
- 权限发布后，`tenant_access_token` 即可访问该用户日历
- 脚本中的 `CALENDAR_ID` 必须更新为用户的个人日历 ID
- 对凌晨活动（如 01:00 开始），应额外添加 cron job 在当天 00:00 特别提醒

### Calendar 日历 API 实现

**⚠️ Token type决定了你能看到什么（2026-05-21 发现）：**
- `tenant_access_token`：仅能看到**由 Hermes Agent app 创建的日程**，用户手动在飞书里创建的日程对 app token 不可见
- `user_access_token`（OAuth 授权）：可看到用户的**所有个人日历事件**

`feishu_calendar.py` 默认使用 `get_tenant_token()`，因此**早上07:00日程提醒可能显示"暂无安排"而用户实际有行程**。查用户真实全部日程必须用 `lark-cli calendar +agenda`（走 OAuth user token 路径）。

**Calendar 幂等性（2026-05-22 发现）：**
`calendar events create` 支持 `idempotency_key` query 参数，避免重复创建：
```bash
lark-cli calendar events create \
  --data '{"summary":"标题","start_time":...,"end_time":...}' \
  --params '{"idempotency_key":"25fdf41b-8c80-2ce1-e94c-de8b5e7aa7e6"}'
```

**⚠️ 日历 API 返回 0 事件 + 401：Token 已过期（2026-05-22 发现）：**
脚本日历事件返回 0，但用户在飞书里有真实日程。原因是 `user_access_token` 已过期（401）。解法见 `references/token-lifecycle.md#token-expiry-401-unauthorized-pattern`。

**Calendar 批量操作（2026-05-22 新发现）：**
| 操作 | 命令 |
|------|------|
| 批量删参与者 | `lark-cli calendar event.attendees batch_delete --data '{"remove_ids":[...]}'` |
| 批量查忙闲 | `lark-cli calendar freebusys list --data '{"time_min":"...","time_max":"...","user_ids":[...]}'` |
| 统计/全量拉取 | 所有 list/search 类命令都支持 `--page-all --page-limit 0` 全量拉取 |

**Calendar 统计：** CLI 本身无 aggregation 功能，但可配合 `jq` 实现：
```bash
lark-cli calendar events search_event --data '{"query":"","time_min":"...","time_max":"..."}' \
  --page-all --page-limit 0 --format json | jq '.data.items | length'
```

详细 API 参考见 `references/calendar-api.md`，OAuth 授权流程见 `references/calendar-oauth-flow.md`，综合 Feishu API 参考见 `references/feishu-api.md`，定时提醒工作流见 `references/cron-reminder-workflow.md`，Token 生命周期管理见 `references/token-lifecycle.md`，Drive 文档幂等查重（`drive files list` + `created_time` 降序取最新）见 `references/drive-idempotent-find.md`。

**💡 关键执行技术**：始终用 `execute_code` + Python `urllib.request` 做 Feishu API 调用，而不是 bash `curl`。原因是：
1. `terminal` 工具可能持有过期的工作目录（如 `/tmp/openclaw-x`），导致所有 bash 命令失败
2. bash 子进程不会加载 `~/.hermes/.env`，`FEISHU_APP_ID`/`FEISHU_APP_SECRET` 不可用
3. `execute_code` 继承 agent 运行时环境，`.env` 变量可直接通过 `os.environ.get()` 访问

详见 `references/api-call-technique.md`。

#### 相关脚本

- `scripts/feishu_calendar.py` — 日程查询脚本，供 cron job 调用。支持 `today`、`tomorrow`、`date:YYYY-MM-DD` 参数。
- `scripts/feishu_token.py` — Token 自动刷新脚本。支持 `refresh`（刷新 token）和 `get`（读取当前 access_token）。由每周 cron job 自动调用。
- `references/permission-management.md` — 权限生命周期管理，含"发布新版本"提醒、App Secret 被重置陷阱、多 scope OAuth 链接构建、Drive API 删除文档等经验（本会话踩坑总结）。

#### 关键配置文件

`~/.hermes/feishu_user_token.json` — 存储用户 refresh_token、open_id、calendar_id。由 OAuth 流程首次写入，后续由 `feishu_token.py` 自动更新。

#### 权限分层

| Scope | 能力 | 适用令牌 |
|-------|------|---------|
| `calendar:calendar:readonly` | 读取日历和事件 | tenant_token + user_token |
| `calendar:calendar` | 新增/修改/删除事件 | 仅 user_token |
| `drive:drive` | CRUD 云空间文件（含删除文档） | tenant_token |
| `drive:drive:readonly` | 读取用户云空间文件列表 | 仅 user_token (OAuth) — ⚠️ 不在推荐域中，需显式请求 |
| `space:document:delete` | 通过 Drive API 删除文档（替代 drive:drive） | tenant_token |
| `wiki:node:update` | 更新 Wiki 节点标题 | 仅 user_token（OAuth scope） |
| `wiki:node:delete` | 删除 Wiki 节点 | 仅 user_token（OAuth scope） |
| `wiki:member:create` | 添加 Wiki 空间成员 | 仅 user_token（OAuth scope） |

- **Wiki 写操作**：必须用 `user_access_token`（OAuth 授权获取），且 token 仅 ~2 小时有效；app token 无法操作用户 wiki（需应用加入空间成员）
- 错误码 `191002` = 写操作用了 tenant_token；`99991668` = user_token 过期；`99991679` = 缺 `wiki:node:update`/`wiki:node:delete` scope
- **写操作**：必须用 `user_access_token`（OAuth 授权获取），且 token 仅 ~2 小时有效
- 错误码 `191002` = 写操作用了 tenant_token；`99991668` = user_token 过期
- **Wiki 写操作**：`wiki update` / `wiki delete` 需要 `wiki:wiki` 权限（user token 的 OAuth scope），app token 无法执行

#### 获取 tenant_access_token
```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"$FEISHU_APP_ID","app_secret":"$FEISHU_APP_SECRET"}'
```

#### 列出日历
```bash
curl -s 'https://open.feishu.cn/open-apis/calendar/v4/calendars?page_size=50' \
  -H 'Authorization: Bearer {TOKEN}'
```
⚠️ `page_size` 最小值为 **50**。传小于 50 的值会报错 `99992402 (field validation failed: "the min value is 50")`。

#### 查询日程事件
```bash
curl -s 'https://open.feishu.cn/open-apis/calendar/v4/calendars/{CALENDAR_ID}/events?page_size=50&start_time={UNIX_TS}&end_time={UNIX_TS}' \
  -H 'Authorization: Bearer {TOKEN}'
```
⚠️ `start_time` / `end_time` 必须用 **Unix 时间戳（秒）**，不能用 ISO 8601 字符串（如 `2026-05-15T20:00:00+08:00`）。用 ISO 格式会报错 `190014: "data type of the start_time field is incorrect"`。

#### 关键权限踩坑

| 现象 | 原因 | 解决 |
|------|------|------|
| `99991672` | 未开通 scope 或已添加但未发布 | ⚠️ 先检查是否**发布了新版本**，这是最常见的遗漏步骤 |
| `99991679` | Wiki 更新/删除：token 缺 `wiki:node:update`/`wiki:node:delete` scope | 在 OAuth 授权 URL 中显式添加这两个 scope 后重新扫码 |
| `wiki spaces` 返回空 | App token 没有加入任何 wiki 空间 | 在飞书 wiki 空间设置中把应用加为成员，或用 user token 的 `wiki member add` |
| tenant token 只能看到 bot 自己的日历 | tenant_access_token 不是用户身份 | 需要 OAuth 用户授权 |
| `20029` 重定向 URL 有误 | OAuth 回调地址未配置 | 在开发者后台→安全设置→重定向 URL 中添加 |
| 页面不存在但授权成功 | 回调页面本就不存在 | 授权码在 URL 参数 `?code=...` 中，让用户复制整个 URL |
| `10014` / `20035` app secret invalid | 用户可能在开发者后台重置了密钥 | 引导用户从开发者后台重新获取 App Secret |

#### `calendar create-event` 必须用 `-c` 指定日历 ID（踩坑记录）

```bash
# ✅ 正确：-c 短标志指定日历
lark-cli calendar create-event -c "$CAL_ID" --summary "标题" --start "$START" --end "$END"

# ❌ 错误：日历 ID 作为位置参数 → "required flag(s) 'calendar-id' not set"
lark-cli calendar create-event "$CAL_ID" --summary "标题" ...
```

**权限管理关键流程（本会话踩坑总结）**

#### ⚠️ 权限管理关键流程（本会话踩坑总结）

**添加任何权限后的黄金法则：必须在开发者后台→版本管理与发布→发布新版本。** 权限在开发者后台勾选后不会立即生效，必须通过发布新版本才能激活。如果用户反馈"加了权限但还是报 99991672"，99% 是漏了发布步骤。

**权限类型区分：**

| 类型 | 添加方式 | 生效条件 | 用途 |
|------|---------|---------|------|
| 应用身份权限（tenant） | 开发者后台→权限管理→添加 | 发布新版本 | 删除文档(`drive:drive`)、知识库只读(`wiki:wiki:readonly`)等 |
| 用户身份权限（OAuth scope） | 在 OAuth URL 的 `scope` 参数中声明 | 用户重新授权 | 列出用户文件(`drive:drive:readonly`)、日历读写等 |

**App Secret 被重置陷阱：** 用户在开发者后台操作（如添加权限、修改安全设置）后，有时 App Secret 会被重置或重新生成。表现为原来可用的 `tenant_access_token` 突然报错 `10014`。这时需要用户重新从开发者后台→凭证与基础信息复制当前 App Secret。

**多权限 OAuth URL 构建：** 多个 scope 用逗号分隔，不转义 URL：
```
https://open.feishu.cn/open-apis/authen/v1/index
  ?app_id={APP_ID}
  &redirect_uri={URI}
  &scope=calendar:calendar:readonly,calendar:calendar,drive:drive:readonly,wiki:wiki:readonly
  &state={STATE}
```

**删除文档权限注意事项：**
- `lark-cli doc delete` 只能删除文档内的块（需 doc_id + block_id），不能删除整个文档
- 删除整个文档需使用飞书 Drive API，且需要 `drive:drive` 或 `space:document:delete` scope
- scope 添加后必须**发布新版本**才生效，仅添加不发布 = 没加

**脚本执行注意事项：**
- 当 curl 请求包含特殊字符（如 JSON body 含 `$`、`"` 等）或嵌套引号时，bash 命令字符串易出问题。此时应改用 `execute_code` Python 环境，使用 `subprocess.run()` 和 `json.dumps()` 来保证参数正确转义。

#### OAuth 授权流程总结

1. 在飞书开发者后台配置重定向 URL（如 `https://httpbin.org/get`）
2. 生成授权 URL：`https://open.feishu.cn/open-apis/authen/v1/index?app_id={APP_ID}&redirect_uri={URI}&scope=calendar:calendar:readonly&state={STATE}`
3. 用户浏览器打开 → 登录授权 → 跳转到 redirect_uri（页面不存在正常）
4. 用户复制跳转后 URL 中的 `code` 参数
5. 用 `POST /open-apis/authen/v1/access_token` 换取 `user_access_token`
6. 保存 `refresh_token` 到 memory 以便后续刷新
7. 用 `user_access_token` 查询用户个人日历
8. 获取用户日历 ID 后，更新 `feishu_calendar.py` 脚本中的 `CALENDAR_ID`

### 任务管理（Task Management）— 详细操作见 `references/feishu-task-commands.md`

**⚠️ 查待办/日程默认路径（重要）：** 当用户问"代办"、"待办"、"我的任务"、"日程安排"时，**默认查飞书**，不查 Hermes 内置 todo 工具（后者对此用户始终为空）。

本技能的任务 Python 封装层（`feishu-task`）提供 7 个功能，开箱即用：

| 操作 | 调用命令 |
|------|---------|
| 查看未完成任务 | `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --completed=false` |
| 统计概览 | `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-task/scripts/stats.py` |
| 搜索任务 | `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-task/scripts/search_tasks.py --query "关键词"` |
| 创建任务 | `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-task/scripts/create_task.py --summary "任务标题" --due "+2d"` |
| 完成任务（模糊匹配） | `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-task/scripts/complete_task.py --query "关键词"` |
| 批量完成 | `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-task/scripts/batch_complete.py --guids "guid1,guid2"` |
| 查看已完成任务 | `lark-cli task tasks list --params '{"completed": true, "page_size": 40}' --format json` |

#### 任务状态验证陷阱（本 session 新增 2026-05-19）：

`lark-cli task +complete` 返回成功 ≠ 任务真的从列表里消失了。**`get-my-tasks` 返回的是完整列表（completed + incomplete 混合）**，即使任务已标记为 done 仍会显示。正确的完成验证命令是：

```bash
# ✅ 正确：过滤出已完成的真实任务
lark-cli task tasks list --completed-status done --page-size 100

# ❌ 错误：get-my-tasks 显示混合列表，无法判断完成状态
lark-cli task get-my-tasks
```

**辨别任务真实状态的字段：** 查 `status` 字段 — `status=done` + 有 `completed_at` 时间戳 = 已完成；`status=todo` + `completed_at=0` = 未完成。

详见 `references/task-completion-verification.md`。

#### 任务 → Skill 封装计划

用户已确认要创建 `feishu-task` skill，功能范围：查看待办（今日/本周/所有）、创建任务、完成任务、清理过期任务、搜索任务。触发方式：自然语言"查看飞书待办"、"创建任务"等。**做之前需与用户确认方案。**

**⚠️ 任务完成验证陷阱（本 session 新增 2026-05-19）：**
`lark-cli task +complete` 返回成功 ≠ 任务真的在列表里消失了。**`get-my-tasks` 返回的是完整列表（completed + incomplete 混合）**，即使任务已标记为 done 仍会显示。正确的完成验证命令是：

```bash
# ✅ 正确：过滤出已完成的真实任务
lark-cli task tasks list --completed-status done --page-size 100

# ❌ 错误：get-my-tasks 显示混合列表，无法判断完成状态
lark-cli task get-my-tasks
```

**辨别任务真实状态的字段：** 查 `status` 字段 — `status=done` + 有 `completed_at` 时间戳 = 已完成；`status=todo` + `completed_at=0` = 未完成。

详见 `references/task-completion-verification.md`。

### lark-cli 集成

**lark-cli**（`@larksuite/cli`，github.com/larksuite/cli）是飞书官方 CLI，已替换原第三方 `lark-cli`（riba2534/lark-cli，已卸载）。配置于 `~/.lark-cli/`。

**职责分工：**
- **日程/提醒/token管理** → 本技能（`feishu`）的 Python 脚本 + cron job
- **文档/知识库/表格/消息/权限/任务** → `lark-cli`（优先使用）

详细 lark-cli 命令语法、坑点、schema 验证记录见 `references/lark-cli-commands.md`。

> 🗺️ **飞书技能栈架构**：三层关系（`productivity/feishu` → `feishu-task` → `lark-cli`）详解见 `references/architecture.md`。

### 任务管理（Task Management）

**⚠️ 查待办/日程默认路径（重要）：** 当用户问"代办"、"待办"、"我的任务"、"日程安排"时，**默认查飞书**，不查 Hermes 内置 todo 工具（后者对此用户始终为空）。

#### 核心命令

| 操作 | 命令 |
|------|------|
| 查看我的待办（全部） | `lark-cli task +get-my-tasks` |
| 查看已完成任务 | `lark-cli task list --completed-status done --page-size 100` |
| 完成任务 | `lark-cli task +complete <guid>` |
| 创建任务 | `lark-cli task +create --summary "标题" [--due "ISO8601"]` |
| 搜索任务 | `lark-cli task +search <关键词>` |
| 查看任务详情 | `lark-cli task tasks <guid>` |

#### 任务状态验证陷阱（本 session 新增）

`lark-cli task +complete` 返回成功 ≠ 任务真的从列表消失了。`+get-my-tasks` 返回的是**完整混合列表**（completed + incomplete 均显示），无法直接判断完成状态。

**正确的完成验证：**
```bash
# ✅ 正确：过滤出已完成任务，看有没有 completed_at 时间戳
lark-cli task list --completed-status done --page-size 100

# ❌ 错误：get-my-tasks 混合列表，无法区分
lark-cli task +get-my-tasks
```

辨别真实状态的字段：`status=done` + `completed_at` 有值 = 已完成；`status=todo` + `completed_at=0` = 未完成。

#### 数据解析示例

```bash
lark-cli task +get-my-tasks | python3 -c "
import json,sys
d=json.load(sys.stdin)
items = d.get('data',{}).get('items',[])
today = '2026-05-22'
overdue, today_t, upcoming = [],[],[]
for t in items:
    due = t.get('due_at','')[:10] if t.get('due_at') else None
    if due and due < today: overdue.append((due, t['summary']))
    elif due == today: today_t.append(t['summary'])
    else: upcoming.append((due, t['summary']))
print('⚠️ 已过期:'); [print(f'  {d} {s}') for d,s in overdue]
print('📋 今日待办:'); [print(f'  ☐ {s}') for s in today_t]
print('📅 近期:'); [print(f'  {d} {s}') for d,s in upcoming[:8]]
"
```

#### 待清理任务处理

用户积压大量过期任务时，先列出全部过期项，确认哪些要清理（标记完成），再执行。避免误删有价值的旧任务。

#### 任务 → Skill 封装计划

用户已确认要创建 `feishu-task` skill，功能范围：查看待办（今日/本周/所有）、创建任务、完成任务、清理过期任务、搜索任务。触发方式：自然语言"查看飞书待办"、"创建任务"等。**做之前需与用户确认方案。**

**⚠️ 任务完成验证陷阱（本 session 新增 2026-05-19）：**
`lark-cli task +complete` 返回成功 ≠ 任务真的在列表里消失了。**`get-my-tasks` 返回的是完整列表（completed + incomplete 混合）**，即使任务已标记为 done 仍会显示。正确的完成验证命令是：

```bash
# ✅ 正确：过滤出已完成的真实任务
lark-cli task list --completed-status done --page-size 100

# ❌ 错误：get-my-tasks 显示混合列表，无法判断完成状态
lark-cli task get-my-tasks
```

**辨别任务真实状态的字段：** 查 `status` 字段 — `status=done` + 有 `completed_at` 时间戳 = 已完成；`status=todo` + `completed_at=0` = 未完成。

详见 `references/task-completion-verification.md`。

### ⚠️ 关键红线：文件操作必须用用户身份

所有云空间文件操作（`file mkdir`、`file move`、`file shortcut`）**必须**使用 `--user-access-token` 参数，否则操作会落在 app 的云空间里，用户看不到。

> **用户明确要求：不创建 .md 文件，所有文档统一使用飞书原生文档（DOCX）存储。** 更新已有文档用 `doc content-update --mode overwrite`，不要用 `drive push`（后者有 bug不会真正覆盖 FILE）。

```bash
TOKEN=$(python3 -c "import json; print(json.load(open('/home/ubuntu/.lark-cli/token.json'))['access_token'])")
UA="--user-access-token $TOKEN"

# ✅ 正确：用户空间创建文件夹
lark-cli file mkdir "我的文件夹" $UA

# ✅ 正确：用户空间移动文档
lark-cli file move <token> --target <folder_token> --type docx $UA

# ✅ 正确：用户空间创建快捷方式
lark-cli file shortcut <token> --target <folder_token> --type docx $UA
```

不加 `--user-access-token` 时操作默认使用 app (tenant) 身份，文件夹和快捷方式建在 app 空间中，用户看不到。

**`drive:drive:readonly` 权限获取：**
标准 `lark-cli auth login --domain drive --recommend` 只申请 `drive:drive.metadata:readonly`，**不包含** `drive:drive:readonly`。要显式通过 `--scope` 申请：

```bash
# 两步模式
lark-cli auth login --scope "auth:user.id:read drive:drive:readonly offline_access" --no-wait --json
# 用户扫码 → 完成后轮询
lark-cli auth login --device-code <device_code> --json
```

### 云空间文件整理（Organize Drive Files）

原则：
- **自己的文档** → `file move` 移入目录（直接挪动文件本身）
- **别人的文档** → `file shortcut` 快捷方式（不改变原位置）
- **slides 类型** → 只能用 `file shortcut`（不支持 move）

文档库 vs 云空间：
- **我的文档库** = 扁平列表，显示所有文档
- **云空间** = 文件夹树状结构

整理流程：
1. 先用 `lark-cli auth login --scope "drive:drive:readonly offline_access"` 获取列表权限
2. 用 `lark-cli api GET /open-apis/drive/v1/files --params '{"folder_token":"<folder_token>"}'` 查看用户空间全貌
3. 检查用户已有的文件夹结构（如果已有 `个人`、`Projects`、`archive` 等，应在此基础上整合而非另起炉灶）
4. 自己的 docx/bitable/sheet 用 `file move` 移入目标文件夹
5. 他人的文档用 `file shortcut` 建快捷方式
6. slides 用 `file shortcut`（不支持 move）

详见 `references/drive-organization.md`。

**权限踩坑（文档删除）：**
`lark-cli doc delete` 只能删除文档内的块（需 doc_id + block_id），**不能删除整个文档**。删除整个文档需用飞书 Drive API：

```bash
curl -s -X DELETE "https://open.feishu.cn/open-apis/drive/v1/files/{DOC_TOKEN}?type=docx" \
  -H "Authorization: Bearer {TOKEN}"
```

但此端点需要 `drive:drive` 或 `space:document:delete` 权限 scope，默认飞书应用通常**未开通**。报错码：`99991672`。如需删除文档，引导用户在开发者后台添加对应权限并重新发布。

**配置验证：**
```bash
# 测试文档创建
lark-cli doc create --title "测试标题"

# 查看配置
lark-cli config list
```

### 复盘文档（每日复盘）— ⚠️ 用户有明确偏好

#### ⚠️ 双端输出设计（2026-05-22 确认版）

复盘 cron job (`20eb32f7bfbb`) 生成两类输出：

**微信推送（stdout）— 执行摘要，一屏扫完：**
```
✅ YYYY-MM-DD 复盘

📋 今日计划
  ✗ 未完成任务标题
  ✓ 已完成任务标题
  （暂无）

⏰ 明日待办
  → 明日待办标题

📅 今日日程
  HH:MM 事项标题
  （暂无）

📄 [HermesAgent/每日复盘/YYYY-MM-DD-复盘总结](链接)
```

**飞书文档（覆盖写入）— 完整结构，有内容才生成：**
```
## 📋 今日计划
来源：昨日「明日待办」+ 今日新增计划

| 时间 | 事项 | 备注 |

## ✅ 今日完成
| 完成 | 未完成 | 调整 |

## ⏰ 明日待办
| 时间 | 事项 | 备注 |

## 📌 待跟进
🔴 紧急  🟡 一般  🟢 缓办
- 未完成任务标题
（有内容才生成此节）

## 📅 后续安排
## 💡 今日收获
## ⚡ 今日感受
（以上三节有内容才生成）
```

**关键规则：**
- **待跟进**：有内容才生成。内容来源 = 今日计划中 `summary` 未出现在今日完成的任务（按标题精确匹配）
- **后续安排/今日收获/今日感受**：有内容才生成
- 日程按时间升序排列，已取消（`status=cancelled`）的日历事件**必须过滤**
- 幂等性：每天只保留 1 个同名文档；`find_doc_in_folder` 按 `created_time` 降序取最新

#### ⚠️ 文档命名规则（2026-05-20 新增：文件名=唯一标识）

**文件名（标题）是复盘文档的唯一标识，不是文档内容。**

- 搜索/查找复盘文档：用 `drive +search` 按文件名搜索（`YYYY-MM-DD-复盘总结`）
- 更新复盘文档前：必须先确认文件名对应的是哪天的内容，避免覆盖错误文档
- 错误案例：用户有「2026-05-19-复盘总结」和「2026-05-20-复盘总结」两个文档，错误地用5/20的内容覆盖了5/19文档
- 正确做法：先 `drive +search` 确认当天文档是否存在，不存在才创建新的

#### 模板格式

每日复盘文档存放在云空间 `HermesAgent/每日复盘/`，命名格式：`YYYY-MM-DD-复盘总结`。

模板板块（严格按此顺序和标题）：

**必须板块：**
| 板块 | 标题 | 说明 |
|------|------|------|
| ✅ 完成事项 | `✅ 完成事项`（表格：时间、事项、备注） | 🟥 核心 |
| ⏰ 明日待办 | `⏰ 明日待办（日期）`（表格：时间、事项） | 🟥 核心，来源标记 |
| 📅 后续安排 | `📅 后续安排`（表格：日期、事项） | 🟧 保留 |
| 💰 待跟进 | `💰 待跟进`（列表，每条一项，可加⏰时间标注紧迫度） | 🟥 核心 |

**可选板块：**
| 板块 | 标题 | 说明 |
|------|------|------|
| 💡 今天学到的 | `💡 今天学到的`（列表） | 🟧 有就写，⚠️ 用「今天学到的」非「今日新发现」 |
| ⚡ 今日高光/感受 | `⚡ 今日高光/感受`（一段话） | 🟨 选填，不强制 |
| 📂 项目速览 | 文档开头的轻量段 | 🟨 仅多个并行项目时自动加，🟢🟡🔴标状态 |

**关键用词偏好（必须遵守）：**
- 板块标题用 **「今天学到的」**，非「今日新发现」
- 文中用 **「待办」**，非「代办」
- 「待跟进」板块标题保持「💰 待跟进」

**官方日程原则：** 赛事/活动官方日程不放入复盘文档，应通过 `lark-cli calendar create-event` 直接更新飞书日历。

### 复盘生成工作流

**⚠️ 文件夹结构注意（2026-05-22 发现）：**
`hermesAgent` 文件夹不在根目录，而是在 `nodcnu9wxEkxzgM53MYnlJXM4Kp` 下。搜索/创建 `hermesAgent` 时必须传入 `parent_token`，否则永远搜不到：
```
HERMES_PARENT_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"
get_folder_token("hermesAgent", HERMES_PARENT_TOKEN)
```

1. 先 `lark-cli auth refresh` 刷新 token
2. 查询用户个人日历获取当日安排
3. 查已有复盘文档是否已存在（用 `drive files list` 在 `hermesAgent/每日复盘` 文件夹中搜索，注意传 parent_token）
4. 如果不存在：`lark-cli docs +create --title "YYYY-MM-DD-复盘总结" --folder-token <daily_token> --markdown " "` → `file move` 到每日复盘文件夹 → `+update --mode overwrite` 填入内容
5. 如果已存在且需更新：`+update --mode replace_range` 或 `--mode overwrite`
6. 注意：lark-cli 创建文档时已设 transfer_ownership=true，自动转移给用户

### 复盘更新方式（⚠️ 表格单元格更新特殊处理）

**普通文本/标题块的更新：**
```bash
lark-cli doc content-update DOC_ID --mode replace_range --selection-by-title "## 标题" --markdown "..."
```

**表格单元格内的文本：** `content-update --selection-with-ellipsis` **无法匹配表格内的文本块**（表格单元格是独立的 block_type=32 容器，其子文本块不参与 selection 匹配）。正确做法：
```bash
# 1. 先获取所有块 ID，找到目标表格单元格的文本块
lark-cli doc blocks DOC_ID --output json

# 2. 用 doc update 直接更新该块
lark-cli doc update DOC_ID BLOCK_ID \
  --content '{"update_text_elements":{"elements":[{"text_run":{"content":"新内容"}}]}}'
```

通用规则：凡遇到 `selection-with-ellipsis` 报"未找到包含起始文本的块"错误，大概率是目标文本在表格单元格内，改用 `doc update` 按 block ID 更新。

### 文档删除

删除文档需要用 Drive API（`lark-cli doc delete` 只能删除文档内的块）：
```bash
lark-cli file delete FILE_TOKEN --type docx --user-access-token TOKEN -f
```

删除整篇文档后，如果存在同名定时任务（如复盘生成 cron），记得暂停/调整 cron job 避免自动重建。使用 `cronjob(action="pause", job_id=...)` 和 `cronjob(action="resume", job_id=...)` 管理。

## Wiki 知识库操作

### 支持的操作

| 操作 | CLI 命令 | 权限要求 |
|------|---------|---------|
| 查看节点 | `wiki get <node_token>` | `wiki:node:read` |
| 列出空间 | `wiki spaces` | `wiki:space:read` |
| 列出节点 | `wiki nodes list --params '{"space_id": "X"}'` | `wiki:space:read` |

### lark-cli 命令语法坑点（2026-05-20 发现，2026-05-22 全面更正）

**drive files 子命令（不能用 +前缀语法）：**
```bash
# ✅ 正确：drive files list（不是 drive +list）
lark-cli drive files list --params '{"folder_token":"<token>"}' --format json

# ✅ 正确：drive files create_folder（不是 drive +create-folder）
# 注意：folder_token 必须传，空字符串表示根目录
lark-cli drive files create_folder --data '{"name":"文件夹名","folder_token":""}' --format json

# ❌ 错误：drive +list / drive +create-folder —— 这些子命令不存在
```

**删除文件/文件夹：**
```bash
# ✅ 正确：--file-token（不是 --file） + --type + --yes
lark-cli drive +delete --file-token <token> --type docx --yes

# ❌ 错误：
lark-cli drive files delete --file <token>   # files delete 子命令不存在
lark-cli drive +delete --file <token>         # 缺 --type
```

**wiki nodes list 参数传递：**
```bash
# ✅ 正确：space_id 通过 --params JSON 传递
lark-cli wiki nodes list --params '{"space_id": "7641316379273989314"}'
# ❌ 错误：--space-id 不是有效 flag
```

**docs +search 参数（2026-05-22 确认）：**
```bash
# ✅ 正确：--query 是搜索词，--format json 输出
lark-cli docs +search --query "关键词" --format json
# ❌ 错误：--folder-tokens、--doc-types 等 flag 不存在
```

**calendar +create 语法：**
```bash
# ✅ 正确
lark-cli calendar +create --calendar-id <id> --summary "标题" --start "ISO8601" --end "ISO8601"
# ❌ 错误：没有 -c 短标志
lark-cli calendar create-event -c <id> ...
```

**calendar events create 幂等 key（2026-05-22 新发现）：**
```bash
# 幂等 key 通过 --params 传入（不是 --data）
lark-cli calendar events create --data '{...}' --params '{"idempotency_key":"uuid"}'
```

**calendar 批量操作（2026-05-22 新发现）：**
```bash
# 批量删除参与者
lark-cli calendar event.attendees batch_delete --data '{"remove_ids":["user_id1","user_id2"]}'

# 批量查询忙闲
lark-cli calendar freebusys list --data '{"time_min":"...","time_max":"...","user_ids":["..."]}'

# 全量翻页：所有 list/search 命令支持 --page-all --page-limit 0
lark-cli calendar events search_event --data '{}' --page-all --page-limit 0
```
```

### 已知限制
| 创建节点 | `wiki create --space-id <id> --title "标题" [--parent-node <token>]` | `wiki:node:create` |
| 移动节点 | `wiki move <node_token> --target-space-id <id>` | `wiki:node:move` |
| 更新节点标题 | `wiki update <node_token> --title "新标题"` | `wiki:node:update` |
| 删除节点 | `wiki delete <node_token>` | `wiki:node:delete` |
| **添加空间成员** | `wiki member add <space_id> --member-type email --member-id xxx --role admin` | `wiki:member:create` |
| 列出空间成员 | `wiki member list <space_id>` | `wiki:member:retrieve` |

### 已知限制

**Wiki 写操作缺权限（`99991679`）：**
`wiki update` 和 `wiki delete` 需要 `wiki:node:update` 和 `wiki:node:delete` 权限。当前的 user token 可能缺少这两个 scope，导致更新/删除节点时报 `Unauthorized`。解法：
1. 用户重新扫码授权，在 OAuth URL 的 scope 参数中显式加上 `wiki:node:update wiki:node:delete`
2. 或者在飞书客户端直接编辑节点标题（绕过 API）

**App token 无法操作 Wiki：**
即便在开发者后台开通了 `wiki:node:update`/`wiki:node:delete` 权限，app token（tenant_access_token）也无法操作用户的 wiki——因为应用没有被加入 wiki 空间成员。解法：
- 在飞书里打开目标 wiki 空间 → 「···」→「空间设置」→「成员管理」→ 添加应用「Hermes Agent」，给编辑权限
- 或者用 user token + `wiki member add` 命令将应用加为空间成员

**Wiki 删除 API 返回 404：**
`DELETE /open-apis/wiki/v2/nodes/{node_token}` 端点对某些节点类型返回 404，改用 `lark-cli wiki delete <node_token>` 交互式删除（会询问确认）。

**Wiki 创建后位置固定：**
`wiki create --parent-node` 只能在同一 space 内指定父节点，不能跨 space 创建。空间间的移动需要 `wiki move` 命令。

**用户搜索找不到人时：**
`lark-cli user search --query "姓名"` 可能搜不到同名用户（通讯录限制）。解法：让用户提供对方手机号（`--mobile`）或邮箱（`--email`）。

## 文档中枢

核心动作：
- 文档摘要：快速压缩长文内容
- 跨文档检索：找结论而不是找文件名
- 更新追踪：谁改了什么，哪些变更值得你看
- 文档到行动：从内容提取结论、风险与待办

### lark-cli 文档更新模式（⚠️ 容易搞错）

`lark-cli docs +update --mode append` 是**追加模式**，每次调用都会在文档末尾新增内容，不会替换已有内容。反复使用会导致版本号暴涨。

**正确的更新方式：** 见 `lark-cli` skill 或 `references/lark-cli-companion.md`。

**最佳实践：**
- 首次创建：`lark-cli docs +create --title <title> --markdown <content> --folder-token <folder_token>`
- 后续更新：`lark-cli docs +update --doc <id> --mode overwrite --markdown <content>`
- **不要重复使用 `+update --mode append`**，会导致内容无限追加
- 结论先行 + 数据支撑 + 给出备选方案

**⚠️ `docs +search` 是全局搜索（2026-05-22 发现）：**
`lark-cli docs +search --query` 是对全云空间搜索，**不认 `--folder-token` 参数**（该参数在 `+search` 子命令中不存在）。在文件夹内精确查重必须用 `drive files list` + 按 `created_time` 降序取最新。详见 `references/drive-idempotent-find.md`。

**⚠️ `docs +create` 的 `--markdown` 必填（2026-05-22 确认）：**
`--markdown` 是必填字段，传空字符串 `""` 会报错 `"--markdown is required"`。必须传空格 `" "` 才能创建空内容文档。`docs +create` **不支持** `--format json`（该 flag 不存在）。

**⚠️ 飞书云空间文件夹搜索必须传 parent_token（踩坑 2026-05-22）：**
部分文件夹（如 `hermesAgent`）不在根目录，而是在某个父文件夹下。在根目录搜索这些文件夹永远返回空。必须先确定文件夹的 parent_token，再搜索：
```python
HERMES_PARENT_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"  # hermesAgent 的父文件夹
get_folder_token("hermesAgent", HERMES_PARENT_TOKEN)  # 搜索时传入 parent_token
```

**⚠️ docs +create 返回格式（2026-05-22 确认）：**
```json
{"ok": true, "data": {"doc_id": "CMeidMn...", "doc_url": "https://..."}}
```
取 doc_id 用 `data.get("data", {}).get("doc_id")`，不是 `data.get("doc_id")`。

### 跨部门协同
- 事实陈述 + 利益对齐 + 降低侵略性

### 团队跟进
- 明确动作 + 保留体面 + 既指出问题也提供支持路径

### 催办与提醒
- 默认私信优先，公开群里避免让对方下不来台
- 根据层级调节语气密度与催促力度

---

## 交互范式

### 场景 A：项目进度追踪
输入："帮我追一下 A 项目的进度。"
输出：提供包含 3 个核心风险、2 个逾期任务及建议催办名单的精炼简报。

### 场景 B：审批催办
输入："查一下谁的审批卡住了，帮我催一下，语气委婉点。"
输出：列出卡点审批、当前节点、建议催办对象，并生成适配语气的提醒文案。

### 场景 C：周报生成
输入："帮我起草这周周报，重点写 A、B 两个项目。"
输出：生成一版可直接修改发送的周报草稿，并标出数据支持点。

### 场景 D：文档检索
输入："我们上次讨论用户留存的结论在哪个文档里？"
输出：返回最相关文档、关键结论摘要及原文位置。

---

## 适用边界

适合用于：
- 群聊情报整理
- 审批预审与催办
- 会议纪要与待办抽取
- 多维表格与文档联动
- 周报、OKR、项目追踪
- 高压协作环境中的信息压缩与动作排序

不适合用于：
- 替代正式法律、财务、合规判断
- 越权访问无权限数据
- 代替真实管理者做最终组织裁决
- 在缺乏上下文时强行生成确定性结论

---

## 安全边界

- **鉴权隔离**：遵守当前账户权限边界
- **私有上下文**：只在你的操作上下文中组织信息
- **最小动作原则**：先建议，再执行；先识别，再触发

## 启动前置检查（Pre-flight Check）

1. **环境检查**：若未检测到 `FEISHU_APP_ID` 或运行时鉴权未就绪，应退回建议模式
2. **权限检查**：若连接器返回权限不足，应提示用户补齐授权
3. **日历权限检查（日程查询专用）**：若用户第一次提出日程相关需求，先尝试获取 token 列出日历：
   - 先查 memory 中是否存有 `refresh_token`，有则用 `authen/v1/refresh_access_token` 刷新 user_access_token 直接查询
   - 无 refresh_token：`99991672` 未授权 → 生成开通链接让用户点击授权 `calendar:calendar:readonly`
   - OAuth 时报 `20029` → 指导配置回调地址
   - 回调页面显示"页面不存在"是正常的，授权码在 URL 的 `?code=...` 参数中
   - 用 `POST /open-apis/authen/v1/access_token`（非 v2）兑换 user_access_token
   - 保存 `refresh_token` 到 memory 以便下次复用
4. **上下文检查**：若任务缺乏必要上下文，应先追问关键变量
5. **分寸检查**：涉及跨部门催办、向上汇报、公开提醒等敏感动作时，应先给出建议文案或请求确认
6. **⚠️ 待办/日程查询默认路径**：当用户说"代办"、"待办任务"、"我的任务"时，**默认查飞书任务**（`lark-cli task tasks list --params '{"completed": false, "page_size": 50}'`），而非 Hermes 内置 todo 工具。Hermes todo 工具对此用户始终为空。
7. **⚠️ 日程查询默认路径**：当用户说"日程"、"日历"、"今天有什么安排"时，**默认查飞书个人日历**（`lark-cli calendar +agenda`，走 OAuth user token），而非 `feishu_calendar.py`（tenant token 仅能看到 app 创建的事件）。

## 数据处理说明

- 本技能本身不定义任何外部数据上报端点
- 摘要、纪要、催办建议应在当前会话与宿主平台私有上下文中完成
- 本技能不应在未经说明的情况下把飞书数据转发到第三方服务
- 数据读取范围严格受限于用户当前权限、宿主平台连接器能力与任务上下文

### 最小动作原则（Least-Action Principle）

**先识别 → 再建议 → 后确认 → 再执行**
