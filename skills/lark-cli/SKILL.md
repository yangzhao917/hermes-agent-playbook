---
name: lark-cli
description: 飞书官方 CLI 工具（larksuite/cli），200+ 命令，覆盖日历、文档、云空间、任务、知识库、表格、邮件等。支持 AI Agent（Hermes/OpenClaw）身份绑定。
version: 1.0.1
---

> ⚠️ **2026-05-22 发现**：此技能曾被移入 `.archive/`，现已恢复。请勿再次归档。
>
> **Token 管理**：lark-cli 自己管理 token（存在 `~/.lark-cli/hermes/cache/`），不依赖 `~/.hermes/feishu_user_token.json`。调用 lark-cli 子进程时无需手动同步 token。
>
> **相关上层技能**：`feishu-task`（任务封装）、`productivity/feishu`（飞书深度集成）均依赖本技能。

## 相关上层技能

**飞书任务管理（推荐优先使用）：**
- `feishu-task`：Python 封装层，7 个功能（列表/创建/完成/删除/逾期预警/统计/搜索），开箱即用
- `feishu-calendar`：Python 封装层，4 个功能（列表/查询/创建/删除），相对日期快捷键，可读输出
- 调用日历脚本：`~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-calendar/scripts/list_events.py --today`
- 调用：`~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --completed=false`

## 相关文件

> 完整 CRUD 实测对比见 `references/cli-crud-comparison.md`
> **飞书日历 API 幂等性 / 批量 / 性能研究（官方文档确认）**见 `references/calendar-idempotency-research.md`
> **lark-cli 日历模块源码分析**（40天分段/2-step创建/attendee前缀/时间戳精度）见 `references/calendar-source-research.md`
> 功能验证记录（增删改查+批量操作）见 `references/skill-functional-test.md`
> 官方 schema 参数验证见 `references/schema-param-check.md`
> **任务列表正确命令（含解析模板）**见 `references/task-list-command.md`
> **任务 schema 官方验证（page_size=100, status=todo/done, delete 语法等）**见 `references/task-schema-confirmed.md`
> **飞书文档导出 + GitHub 知识库建设工作流**见 `references/playbook-export-workflow.md`

## 工具定位

| 项目 | 说明 |
|------|------|
| **npm 包** | `@larksuite/cli` |
| **源码** | github.com/larksuite/cli |
| **版本** | v1.0.33+ |
| **协议** | MIT |
| **命令前缀** | `lark-cli`（不是 `feishu-cli`） |

## 安装

```bash
# npm 全局安装
npm install -g @larksuite/cli

# 验证
lark-cli --version
```

## Hermes 绑定（必须）

```bash
# 绑定到当前 Hermes 会话
lark-cli config bind --source hermes --identity user-default

# 解绑（清除凭证）
lark-cli config remove
```

**两种身份模式：**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `bot-only` | 机器人身份，无法访问用户个人资源 | 通用工具操作 |
| `user-default` | 操作用户身份（个人日历/云文档/任务等） | 需要操作用户数据时 |

**用户明确要求操作用户个人数据（日历/文档），必须用 `user-default`。**

## 授权登录（OAuth Device Flow）

```bash
# 方式一：推荐 — 先获取链接发给用户，等用户说"好了"再轮询
lark-cli auth login --recommend --no-wait
# 输出 verification_url 和 user_code → 转发给用户

# 用户授权完成后：
lark-cli auth login --device-code <device_code>

# 方式二：阻塞模式（需要 120s+ timeout）
lark-cli auth login --recommend
```

**device_code 10 分钟内有效，超时需重新生成。**

**Token 自动续期：lark-cli 没有 `auth refresh` 命令**，OAuth token 自动续期，无需手动操作。如果 token 失效，重新 `lark-cli auth login`。

## 常用命令速查

### 日历

```bash
# 查看日程（默认今天）
lark-cli calendar +agenda

# 创建日程
lark-cli calendar +create \
  --summary "标题" \
  --start "2026-05-20T10:00:00+08:00" \
  --end "2026-05-20T11:00:00+08:00"

# 删除日程（需 --params 传 calendar_id 和 event_id）
lark-cli calendar events delete \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn", "event_id": "xxx"}'

# 查询 free/busy
lark-cli calendar +freebusy --user-ids ou_5b875f5ec5752b06832bb240ad482ec0 --start "2026-05-20T00:00:00+08:00" --end "2026-05-20T23:59:59+08:00"

# 修改日程（用 events patch，不是 events update）
lark-cli calendar events patch \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn", "event_id": "<event_id>"}' \
  --data '{"summary": "新标题", "start_time": {"timestamp": "1779170400", "timezone": "Asia/Shanghai"}, "end_time": {"timestamp": "1779171000", "timezone": "Asia/Shanghai"}}'

# ⚠️ 时间戳必须用 Python 动态计算，禁止手算
# ✅ 正确：python3 -c "from datetime import datetime,timezone,timedelta; print(int(datetime(2026,5,20,0,0,0,tzinfo=timezone(timedelta(hours=8))).timestamp()))"
# ❌ 错误：凭推算写死时间戳，容易搞错月份/日期

# 获取单个日程
lark-cli calendar events get \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn", "event_id": "<event_id>"}'
```

## 任务列表的正确方式

**⚠️ `+list` 对任务模块不是合法子命令（2026-05-20 实测）：**
```bash
# ❌ 错误：unknown subcommand "+list" for "lark-cli task"
lark-cli task +list

# ✅ 正确：用 tasks list + --params completed 过滤
lark-cli task tasks list --params '{"completed": false, "page_size": 50}' --format json
lark-cli task tasks list --params '{"completed": true, "page_size": 50}' --format json
```

**正确流程：操作任务/日历前必须先 `skill_view(name='lark-cli')`，禁止凭记忆直接敲命令。**

---

### 按时间范围查日程（本周/本月）

不存在 `calendar events list` 命令，正确做法是 `instance_view` + Unix 时间戳：

```python
from datetime import datetime, timezone, timedelta

sh_tz = timezone(timedelta(hours=8))
# 今天 00:00 → 23:59 CST
today_start = datetime(2026, 5, 19, 0, 0, 0, tzinfo=sh_tz)
today_end = datetime(2026, 5, 19, 23, 59, 59, tzinfo=sh_tz)

start_ts = int(today_start.timestamp())
end_ts = int(today_end.timestamp())

print(f"start: {start_ts}, end: {end_ts}")
```

```bash
# 用查到的 ts 查日程
lark-cli calendar events instance_view \
  --params "{\"calendar_id\": \"feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn\", \"start_time\": \"<ts>\", \"end_time\": \"<ts>\"}" \
  --format json 2>&1 | python3 -c "
import json, sys
from datetime import datetime, timezone, timedelta
sh_tz = timezone(timedelta(hours=8))
data = json.loads(sys.stdin.read())
items = data.get('data', {}).get('items', [])
for e in sorted(items, key=lambda x: x['start_time']['timestamp']):
    ts = int(e['start_time']['timestamp'])
    dt = datetime.fromtimestamp(ts, tz=sh_tz)
    print(f'{dt.strftime(\"%m/%d %H:%M\")} | {e.get(\"summary\", \"(无标题)\")}')
"
```

### 任务列表过滤的关键区别

**⚠️ `+get-my-tasks` 和 `tasks list` 是两个不同的 API，行为完全不同：**

| 命令 | 行为 |
|------|------|
| `task +get-my-tasks` | 返回**所有任务**（已完成+未完成混杂），不支持按完成状态过滤 | `due_at`（ISO 字符串） |
| `task tasks list --params '{"completed": false}'` | ✅ 正确：布尔值过滤，返回纯未完成 | `due`（对象，毫秒时间戳） |
| `task tasks list --params '{"completed": true}'` | ✅ 正确：布尔值过滤，返回纯已完成 | `due`（对象，毫秒时间戳） |
| `task tasks list --params '{"completed_status": "not_started"}'` | ❌ 错误：completed_status 不是合法过滤参数（2026-05-20 亲测） | - |

**`completed` 参数说明（2026-05-20 官方 schema 验证）：**

```python
# ✅ 正确：查所有任务，按 status 字段区分
lark-cli task tasks list --params '{"completed": true, "page_size": 40}' --format json
lark-cli task tasks list --params '{"completed": false, "page_size": 40}' --format json
```

```python
# ✅ 正确的过滤逻辑
for t in items:
    if t.get('status') == 'todo':  # 只看 status 字段
        # 真正未完成的任务
    elif t.get('status') == 'done':
        # 已完成（即使出现在 not_started 结果中也别慌）
```

**真正未完成的任务（status=todo，2026-05-21 统计）：**
- 购买IN客松返程车票（2026-05-21）
- 购买IN客松开票车票（去程）（2026-05-21）
- CSS播客重录 🎙️（2026-05-22）
- 毕业生信息采集待上网 📋（2026-05-23）
- 交付Hermes日程管理给卢佩健 💰100（2026-05-24）
- AMD应用开发者大赛：寄回复赛设备（2026-05-24）
- IF.Land AI Hackathon 校内赛 🎪（2026-06-05）
- 哈尔滨复赛聚餐垫付700元 💰（2026-06-19）

| 命令 | 行为 | due 字段 |
|------|------|---------|
| `task +get-my-tasks` | 返回**所有任务**（已完成+未完成混杂），不支持按完成状态过滤 | `due_at`（ISO 字符串，如 `"2026-06-05T00:00:00+08:00"`） |
| `task tasks list` | 按 **`completed`**（布尔值）过滤，返回纯已完成或纯未完成 | `due`（对象，如 `{"is_all_day": false, "timestamp": "1780588800000"}`，毫秒级） |

**踩坑（2026-05-19）：** 解析 `tasks list` 输出时误用了 `due_at`（ISO 字符串），但 `tasks list` API 返回的字段是 `due`（对象）。导致所有截止日期错误显示为"无期限"。

**正确解析 `tasks list`（截止日期）：**
```python
due_ts = t.get('due', {}).get('timestamp', '0')
due_str = datetime.fromtimestamp(int(due_ts)/1000, tz=sh_tz).strftime('%m/%d') if due_ts and due_ts != '0' else '无期限'
```

**正确解析 `+get-my-tasks`（截止日期）：**
```python
due = t.get('due_at', '')
due_str = datetime.fromisoformat(due[:19]).strftime('%m/%d') if due else '无期限'
```

**正确做法：**
```bash
# 查真正的未完成任务
lark-cli task tasks list --params '{"completed": false, "page_size": 40}' --format json

# 查真正的已完成任务
lark-cli task tasks list --params '{"completed": true, "page_size": 40}' --format json
```

---

### 时间戳计算必须用 Python（禁止手算）

**规则：所有日期/时间戳/数学计算，一律用 Python 工具动态计算，禁止手算或硬编码。**

CST 00:00 对应 UTC 前一天 16:00，心算极容易出错：
```python
# ✅ 正确：用 Python 动态计算
from datetime import datetime, timezone, timedelta
sh_tz = timezone(timedelta(hours=8))
dt = datetime(2026, 5, 19, 0, 0, 0, tzinfo=sh_tz)
print(int(dt.timestamp()))  # 1779120000

# ❌ 错误：手算 1779206400，实际是 May 20（差了一天！）
```

> ⚠️ **所有计算（包括数学公式、汇率、比例、日期推算）一律用 Python 工具执行。**

**用户个人日历 ID：** `feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn`

### 文档

```bash
# 创建文档（必须带 --markdown）
lark-cli docs +create \
  --title "文档标题" \
  --markdown "# 标题\n\n内容"

# 搜索文档
lark-cli docs +search --query "关键词"

# 获取文档内容（--doc 是 flag，不是位置参数）
lark-cli docs +fetch --doc <doc_id>

# 更新文档内容（必须指定 --mode）
lark-cli docs +update --doc <doc_id> --markdown "# 新标题\n\n新内容" --mode overwrite
```

### 云空间

```bash
# 上传文件（必须是相对路径，不能用 /tmp/xxx）
cd /tmp && lark-cli drive +upload --file ./myfile.txt --name "文件名.txt"

# 搜索文件
lark-cli drive +search --query "关键词"

# 删除文件
lark-cli drive +delete --file-token <token> --type <file|docx|sheet|slides|bitable> --yes
```

**`task.tasks.list` 官方 schema 参数（2026-05-20 验证）：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `completed` | boolean | ❌ | ✅ 正确过滤参数：`true`=已完成，`false`=未完成 |
| `agent_task_status` | integer | ❌ | 智能体任务状态细分（1-4） |
| `page_size` | integer | ❌ | 默认50 |
| `page_token` | string | ❌ | 分页标记 |
| `type` | string | ❌ | 只支持 `"my_tasks"` |

> ⚠️ **2026-05-22 实测修正：批量完成任务时，`+complete` 成功返回 `{"ok": true}`（不是 `{"code": 0}`）。判断是否成功应 `grep '"ok": true'`。详见 `references/task-batch-complete-quirks.md`。

**`task +complete` / `+reopen` 语法：**
```bash
# ✅ 正确
lark-cli task +complete --task-id <guid>
lark-cli task +reopen   --task-id <guid>

# ❌ 错误：位置参数不支持
lark-cli task +complete <guid>
```

**`task +search` 语法：**
```bash
# --completed 是 flag（不是 --complete）
lark-cli task +search --completed --query "关键词"   # 已完成
lark-cli task +search --completed false --query "关键词"  # 未完成
```

**`task.tasks.patch` update_fields 白名单（status 不在其中）：**
`summary`, `description`, `start`, `due`, `completed_at`, `extra`, `custom_complete`, `repeat_rule`, `mode`, `is_milestone`, `custom_fields`

> ⚠️ `status` **不在**白名单中，标记完成只能用 `+complete --task-id`，不能用 patch

**`task due` 时间戳：毫秒级**（`tasks list` API 返回 `due.timestamp` 是毫秒）

**`task +create` 关键 flag：**
```bash
--summary  # 标题（不是 --name）
--due      # 截止时间，ISO 8601 格式（不是毫秒时间戳）
--assignee # 必须指定，否则用户在飞书里看不到任务
```

---

### 日历

**`calendar +agenda`（查看日程）：**
```bash
# --start/--end 是 ISO 8601 格式（默认今天）
lark-cli calendar +agenda --start "2026-05-20T00:00:00+08:00" --end "2026-05-20T23:59:59+08:00"
lark-cli calendar +agenda --calendar-id "feishu.cn_xxx@group.calendar.feishu.cn"
```

**`calendar +freebusy`（查询忙闲）：**
```bash
lark-cli calendar +freebusy --user-id ou_5b875f5ec5752b06832bb240ad482ec0 --start "2026-05-20T00:00:00+08:00" --end "2026-05-20T23:59:59+08:00"
```

**`calendar +create`（创建日程）：**
```bash
lark-cli calendar +create \
  --summary "标题" \
  --start "2026-05-20T10:00:00+08:00" \
  --end "2026-05-20T11:00:00+08:00" \
  --attendee-ids "ou_xxx,ou_yyy" \
  --calendar-id "feishu.cn_xxx@group.calendar.feishu.cn"
```

**`calendar events patch / delete`（修改/删除日程）：**
- 路径参数（calendar_id、event_id）**必须**放 `--params` JSON 中
- Body 数据放 `--data` JSON
- **不是**位置参数！

```bash
# ✅ 正确
lark-cli calendar events patch \
  --params '{"calendar_id": "feishu.cn_xxx", "event_id": "<event_id>"}' \
  --data '{"summary": "新标题", "start_time": {"timestamp": "1779170400", "timezone": "Asia/Shanghai"}, "end_time": {"timestamp": "1779171000", "timezone": "Asia/Shanghai"}}'

lark-cli calendar events delete \
  --params '{"calendar_id": "feishu.cn_xxx", "event_id": "<event_id>"}'

# ❌ 错误：位置参数不支持
lark-cli calendar events patch <calendar_id> <event_id> --data '...'
```

> ⚠️ `calendar events patch` 的 `--data @file` 必须用**相对路径**，不能用绝对路径

**时间戳规则：**
- 日历 `start_time.timestamp` / `end_time.timestamp`：**秒级 Unix 时间戳**
- 任务 `due.timestamp`：**毫秒级 Unix 时间戳**
- 计算一律用 Python，禁止手算：
```python
# 日历（秒）
int(datetime(2026,5,20,10,0,0,tzinfo=timezone(timedelta(hours=8))).timestamp())

# 任务（毫秒）
int(datetime(2026,5,20,10,0,0,tzinfo=timezone(timedelta(hours=8))).timestamp() * 1000)
```

---

### 表格

```bash
# 创建表格
lark-cli sheets +create --title "表格标题"

# 读取表格
lark-cli sheets +read <sheet_token> "Sheet1!A1:C10"

# 写入表格（--token, --sheet, --range, --value 都是 flag）
lark-cli sheets +write \
  --token <sheet_token> \
  --sheet "Sheet1" \
  --range "A1:B2" \
  --value '[["姓名","年龄"],["张三",25]]'
```

### 知识库

```bash
# 列出知识空间
lark-cli wiki spaces list

# 列出节点
lark-cli wiki nodes list --params '{"space_id": "<id>"}'

# 创建节点
lark-cli wiki +node-create --space-id <id> --title "标题" --parent-node <parent_token>
```

### ⚠️ 硬约束：操作前必须加载 skill

**禁止凭记忆直接敲命令。** 每一次飞书操作前必须先 `skill_view(name='lark-cli')`，获取最新命令语法。

**本次 session 踩坑（2026-05-20）：**
- 错误使用了 `lark-cli task +list`（不是合法子命令）→ JSON parse 失败 → 误判所有任务被删除
- 正确命令：`lark-cli task tasks list --params '{"completed": false, "page_size": 50}' --format json`
- 教训：即使熟悉的命令，也要先读 skill 确认

---

## 命令规律

| 模块 | 创建 | 删除 | 重要 flag |
|------|------|------|----------|
| calendar | `+create` | `events delete`（需 `--params`） | 修改用 `events patch`，需 `--params` + `--data` JSON；`--start/--end` 仅用于 `+create` |
| docs | `+create`（需 `--markdown`） | `drive +delete --type docx` | `+update` 需 `--mode overwrite`，用 `--doc` 传参；`+fetch` 也用 `--doc` |
| drive | `+upload`（相对路径） | `+delete --type` | `--file-token`，不是位置参数 |
| task | `+create` | `tasks delete --params '{"task_guid":"<guid>"}' --yes` | `+complete --task-id <guid>` | 列表用 `tasks list`；`--task-id` 是 flag；`tasks patch` 需 `update_fields` |
| sheets | `+create` | 无 CLI 命令 | 读/写用 `--token/--sheet/--range/--value` |
| wiki | `+node-create` | 无 CLI 命令 | |

## 踩坑记录

### drive +upload 必须用相对路径

```bash
# ❌ 错误
lark-cli drive +upload --file /tmp/test.txt --name "test.txt"

# ✅ 正确（cd 到文件所在目录）
cd /tmp && lark-cli drive +upload --file ./test.txt --name "test.txt"
```

### docs +create 必须传 --markdown

```bash
# ❌ 报错：--markdown is required
lark-cli docs +create --title "标题"

# ✅ 正确
lark-cli docs +create --title "标题" --markdown "# 标题\n\n内容"
```

### docs +update 必须指定 --mode

```bash
# ❌ 报错：--mode is required
lark-cli docs +update --doc <doc_id> --markdown "新内容"

# ✅ 正确
lark-cli docs +update --doc <doc_id> --markdown "# 标题\n\n内容" --mode overwrite
```

**⚠️ overwrite 模式是全量覆盖，不是追加。2026-05-20 踩坑：搜索 "2026-05-20-复盘总结" 找到了5/19创建的文档（BCUodnNMkojmuoxkWP3cOcPrndf），误以为它是今天的，用 overwrite 把5/19内容覆盖成了5/20。**

**教训（2026-05-20）：用 `drive +search` 搜 "2026-05-20-复盘总结" 找到了5/19创建的文档（BCUodnNMkojmuoxkWP3cOcPrndf，00:01创建但内容是5/19），直接 overwrite 把5/19内容覆盖成了5/20。**

**根因**：`drive +search` 返回的是文档的创建时间，而不是文档内容对应的日期或文档标题中的日期。

**正确流程**：
1. `drive +search` 找到候选文档
2. 用 `docs +fetch --doc <doc_id>` 查看实际内容，确认日期
3. 再决定是 `docs +update`（追加/覆盖）还是 `docs +create`（新建）
4. **绝不能仅凭 search 结果中的标题/时间戳直接判断**

支持的 mode：`append`、`overwrite`、`replace_range`、`replace_all`、`insert_before`、`insert_after`、`delete_range`。常用 `overwrite`。

### docs +fetch --doc 是 flag 不是位置参数

```bash
# ❌ 错误：positional arguments not supported
lark-cli docs +fetch ZSJldcpUFokm1lxGQlhcZM9Xndc

# ✅ 正确
lark-cli docs +fetch --doc ZSJldcpUFokm1lxGQlhcZM9Xndc
```

> ⚠️ docs 系列命令（+create/+fetch/+update/+search）均使用 v1 API，输出会显示 `[deprecated]` 但功能正常。文档删除无专属命令，需用 `drive +delete --type docx`。

### docs +fetch 输出含 [deprecated] 前缀，导致 JSON 解析失败

```bash
# ❌ 直接 pipe 到 python -c "json.loads(sys.stdin.read())" 会失败
lark-cli docs +fetch --doc <doc_id> 2>&1 | python3 -c "import json,sys; json.loads(sys.stdin.read())"
# → JSONDecodeError: Expecting value: line 1 column 2

# ✅ 正确方法一：用 tail -20 取输出后半部分（去掉 [deprecated] 行）
lark-cli docs +fetch --doc <doc_id> 2>&1 | tail -20

# ✅ 正确方法二：用 --format json 明确指定输出格式（部分命令支持）
lark-cli docs +fetch --doc <doc_id> --format json 2>&1 | tail -20
```

**根因**：`lark-cli` 输出 `[deprecated]` 到 stderr，Python 读取时整行成为 JSON 字符串前缀，导致解析失败。

### --data @file JSON 数据必须用相对路径

`calendar events patch` 的 `--data` 参数如果使用 `@file.json` 方式传入 JSON，**文件必须是相对路径**，且必须在当前工作目录下：

```bash
# ❌ 错误：绝对路径报错
lark-cli calendar events patch \
  --params '{"calendar_id": "...", "event_id": "..."}' \
  --data @/tmp/patch_event.json
# → invalid file path "/tmp/patch_event.json" --file must be a relative path within the current directory

# ✅ 正确：先把文件复制到当前目录，再用相对路径
cp /tmp/patch_event.json ./patch_event.json
lark-cli calendar events patch \
  --params '{"calendar_id": "...", "event_id": "..."}' \
  --data @./patch_event.json
```

> 同样的限制也适用于 `drive +upload --file`（已有记录），是 lark-cli 的通用约束。

### WeChat 图片下载后格式识别问题

WeChat 通过平台发送的图片，下载到 `~/.hermes/image_cache/` 后可能扩展名(.jpg)和实际格式(PNG)不匹配。vision 工具依赖文件头判断格式，扩展名错误会导致分析失败。

**检测方法**：
```bash
file /path/to/image.jpg  # 可能输出 "PNG image data" 而非 "JPEG image data"
```

**影响**：使用 `vision_analyze` 时图片明明存在但工具返回"看不到图片"。

**临时方案**：暂不处理，等用户重新截图发送。

`calendar events patch` 的 `--data` 参数如果使用 `@file.json` 方式传入 JSON，**文件必须是相对路径**，且必须在当前工作目录下：

```bash
# ❌ 错误：绝对路径报错
lark-cli calendar events patch \
  --params '{"calendar_id": "...", "event_id": "..."}' \
  --data @/tmp/patch_event.json
# → invalid file path "/tmp/patch_event.json" --file must be a relative path within the current directory

# ✅ 正确：先把文件复制到当前目录，再用相对路径
cp /tmp/patch_event.json ./patch_event.json
lark-cli calendar events patch \
  --params '{"calendar_id": "...", "event_id": "..."}' \
  --data @./patch_event.json
```

> 同样的限制也适用于 `drive +upload --file`（已有记录），是 lark-cli 的通用约束。

### search_event 搜不到已知日程

`calendar events search_event` 按 keywords 搜索经常返回 0 结果，即使日程实际存在。**查指定日程的正确方式是直接用 `events get` + event_id**（需要已知 event_id）。

```bash
# ❌ 搜不到
lark-cli calendar events search_event --params '{"keywords":["过道对白"]}'
# → 0 results

# ✅ 直接查
lark-cli calendar events get \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn", "event_id": "d721c65a-7995-495f-a838-18cb496f5226_0"}'
```

### JSON 解析通用模式（`--format json` 输出含 `[deprecated]` 前缀）

所有返回 `--format json` 的命令都可能遇到 `[deprecated]` 前缀导致 `json.loads()` 失败。正确解析模式：

```python
import json, subprocess

result = subprocess.run(["lark-cli", "calendar", "events", "instance_view",
                        "--params", json.dumps(params), "--format", "json"],
                       capture_output=True, text=True)
try:
    data = json.loads(result.stdout)
except json.JSONDecodeError:
    # 尝试逐行找有效 JSON（跳过 [deprecated] 等前缀行）
    for line in result.stdout.strip().split("\n"):
        try:
            data = json.loads(line)
            break
        except:
            continue
    else:
        raise RuntimeError(f"无法解析输出: {result.stdout[:200]}")
```

> 2026-05-22 实测：calendar `instance_view`、`events get`、`+create` 均会遇到此问题，文档命令（docs 系列）也有。通用处理逻辑应覆盖所有 `--format json` 输出。

### events delete/patch 需要 --params（不能用位置参数）

所有 `events` 子命令（delete、patch、get）**不接受位置参数**，路径参数（calendar_id、event_id）必须通过 `--params` 传入：

```bash
# ❌ 错误：missing required path parameter: calendar_id
lark-cli calendar events delete <calendar_id> <event_id>
lark-cli calendar events patch <calendar_id> <event_id> --data '...'

# ✅ 正确：路径参数放 --params（JSON 中 event_id 是 snake_case），body 数据放 --data
lark-cli calendar events delete \
  --params '{"calendar_id": "<cal_id>", "event_id": "<event_id>"}'

lark-cli calendar events patch \
  --params '{"calendar_id": "<cal_id>", "event_id": "<event_id>"}' \
  --data '{"start_time": {"timestamp": "1779206400", "timezone": "Asia/Shanghai"}, "end_time": {"timestamp": "1779292799", "timezone": "Asia/Shanghai"}}'
```

**⚠️ 重要细节：**
- `--params` JSON 中字段名是 **`event_id`**（snake_case），不是 camelCase
- `--event-id` 这样的 flag **不存在**，不要用
- patch 更新部分字段时只需传想改的字段，不一定要传全部字段

### task +complete --task-id 是 flag 不是位置参数

```bash
# ❌ 错误：positional arguments not supported
lark-cli task +complete <guid>

# ✅ 正确
lark-cli task +complete --task-id <guid>
```

**批量完成多个任务：必须串行循环，每次单独调用 `--task-id`**：

```bash
# ✅ 正确：串行执行，每次一个 --task-id
for guid in $LIST_OF_GUIDS; do
  lark-cli task +complete --task-id "$guid" 2>&1
done

# ❌ 错误：传多个 guid 到位置参数（只有第一个被执行，其余全部跳过）
for guid in $LIST_OF_GUIDS; do
  lark-cli task +complete "$guid"  # ← 每次循环这个 guid 成为位置参数，不是 --task-id
done
```

**判断成功的标志是 `ok: true`（不是 `code:0`）：**
```bash
r=$(lark-cli task +complete --task-id "$guid" 2>&1)
echo "$r" | grep -q '"ok": true' && echo "OK" || echo "FAIL"
```
> ⚠️ 本 session（2026-05-20）踩坑：`+complete` 成功返回 `{"ok": true, ...}`，`tasks list` API 成功返回 `{"code": 0, ...}`。两者不同！

**⚠️ `+get-my-tasks` 默认返回已完成+未完成，**`--complete false` 语法不生效**：**

```bash
# ❌ --complete false 会报 Usage（flag 解析错误）
lark-cli task +get-my-tasks --complete false  # → exit 1，输出帮助文本

# ✅ 正确做法：用 tasks list 按状态过滤
lark-cli task tasks list --params '{"completed": false, "page_size": 40}' --format json

# ✅ 查已完成任务
lark-cli task tasks list --params '{"completed": true, "page_size": 40}' --format json
```

详见 `references/task-complete-flag-syntax.md` 和 `references/task-batch-complete-quirks.md`。

### ⚠️ 致命陷阱：任务模块 `+list` 子命令不存在（2026-05-20 新增）

```bash
# ❌ 致命错误：unknown subcommand "+list" — 命令不存在！
lark-cli task +list              # → JSON parse 失败，误以为任务被清空

# ✅ 正确：用 tasks list（注意是空格不是加号）
lark-cli task tasks list --params '{"completed": false, "page_size": 50}' --format json
```

**这条命令写错的后果**：API 返回 error JSON，Python `json.load()` 抛 `JSONDecodeError`，之后所有任务显示逻辑崩溃。**恢复方法**：用正确的 `tasks list` 命令重新查询。

**硬规矩**：执行任何 lark-cli 任务/日历操作前，必须先 `skill_view(name='lark-cli')` 确认命令语法。禁止凭记忆直接敲。

**Cron/自动化 session 额外建议**：定时复盘等自动任务执行前，建议用 `session_search` 拉取前 1～3 条相关会话摘要（如前一天复盘、最近的飞书操作记录），帮助判断今日是否有特殊上下文需要纳入复盘内容。

### 批量完成任务时不要用并行（输出交织无法判断成败）

```bash
# ❌ 并行 xargs -P20：输出交织，误报16个"失败"实际全部成功
printf '%s\n' "${cmds[@]}" | xargs -P20 -I{} bash -c "{}"

# ✅ 正确：串行执行，出错立即可见
# ✅ 成功判断：grep '"ok": true'（不是 '"code": 0'！）
for g in "${expired_guids[@]}"; do
  r=$(lark-cli task +complete --task-id "$g" 2>&1)
  if echo "$r" | grep -q '"ok": true'; then
    echo "OK: $g"
  else
    echo "FAIL: $g"
  fi
done
```

> ⚠️ **`+complete` 成功响应是 `{"ok": true, ...}`，不是 `{"code":0, ...}`！用 `grep '"code": 0'` 会误判所有请求为失败。

### drive +delete 需要 --type 和 --yes

```bash
lark-cli drive +delete --file-token <token> --type docx --yes
```

## 用户信息

- 用户名：澄澈少年
- OpenID：ou_5b875f5ec5752b06832bb240ad482ec0
- 个人日历 ID：`feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn`

## 触发条件

当用户提到以下内容时激活：
- 飞书日历/日程操作
- 飞书文档创建/编辑
- 飞书云空间文件操作
- 飞书任务/待办操作
- 飞书知识库操作
- 飞书表格操作
- 任何飞书开放平台 API 操作
