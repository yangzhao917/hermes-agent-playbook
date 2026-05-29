---
name: morning-reminder
description: 每日晨间日程提醒（今日日程 + 今日待办 + 明日预告）
version: 2.0.0
category: productivity
tags: [feishu, calendar, task, reminder, daily, agenda]
---

# ☀️ morning-reminder

> 每日晨间推送飞书日历摘要（今日日程 + 今日待办 + 明日预告），并按 `personal-os-roles` 输出三角色行动建议。

## ⚠️ 禁区

- **触发后必须先 `skill_view(name='morning-reminder')`，再执行脚本**。不允许绕过 skill 直接拼 lark-cli 命令。
- **禁止直接拼 lark-cli 命令**，必须走 feishu-calendar / feishu-task 脚本
- **禁止手算时间戳/日期**，用 Python datetime 计算
- 解析 JSON 必须用两层策略（整段优先 + 逐行 fallback）

## 已知陷阱

### ⭐ script 模式双副本问题
cron job `3adeb578f5bf` 用的是 `~/.hermes/scripts/morning_reminder.py`（script 模式），而 skill 目录是 `~/.hermes/skills/morning-reminder/scripts/`。
**每次更新 skill 里的脚本后，必须同步覆盖 scripts/ 路径**：

```bash
cp ~/.hermes/skills/morning-reminder/scripts/morning_reminder.py ~/.hermes/scripts/morning_reminder.py
```

验证方法：手动跑 `python3 ~/.hermes/scripts/morning_reminder.py` 确认输出正确。

### ⭐ Skill 名称冲突问题
`~/.hermes/skills/` 下可能存在多个同名 skill 副本（如 `daily-review` 同时存在于根目录和 `productivity/` 子目录），导致 Hermes agent 报"Ambiguous skill name"。

**解法**：
- cron job 始终设置 `workdir: "/home/ubuntu/.hermes"`，让 agent 优先从 `~/.hermes/skills/` 解析 skill
- 如果技能名称冲突，用完整相对路径指定（如 `productivity/daily-review` 而非 bare `daily-review`）
- 检查 `~/.hermes/skills/` 下是否有重复命名的 skill 目录，删除不用的那个

### ⭐ 日期解析：必须剥离星期后缀
`list_tasks.py` 输出格式为 `MM/DD 周X`（带空格），两处日期解析必须先 split 取日期部分再处理：

```python
# ❌ 错误：直接取 [3:] 会截到 "周三"
due_month, due_day = int(due_str[:2]), int(due_str[3:])

# ✅ 正确：先按空格分割取日期部分
due_mmdd = due_str.split(" ")[0]
due_month, due_day = int(due_mmdd[:2]), int(due_mmdd[3:])
```
# ✅ 正确：先按空格分割取日期部分
due_mmdd = due_str.split(" ")[0]
due_month, due_day = int(due_mmdd[:2]), int(due_mmdd[3:])
```

两处都需修复：`fetch_todos()` 解析逾期天数 + `classify_tasks()` 判断是否今天截止。

### ⭐ 正则匹配任务行时 emoji 可能紧贴标题文字
`list_tasks.py` 输出示例：`○ CSS播客重录 🎙️  截止 05/27 周三`

非贪婪 `.+?` 遇到 emoji 会提前终止，需用 `\S` + 混合空格字符匹配标题：

```python
# ❌ 错误：非贪婪遇到 emoji 时提前截断
m = re.match(r"^○\s+(.+?)\s+截止\s+...", line)

# ✅ 正确：允许 emoji 作为标题一部分
m = re.match(r"^○\s+(\S(?:\S|\s)*?)\s+截止\s+...", line)
```

### `+agenda` 返回包装格式
`lark-cli calendar +agenda --format json` 返回 `{"ok": true, "data": [...]}` **不是裸数组**。
直接 `isinstance(data, list)` 判断永远为 `False`，导致日程查不到。
修复：取 `data["data"]` 而非直接返回 `data`。

### `start_time` 是嵌套对象
`+agenda` 返回的 `start_time` 是 `{"datetime": "2026-05-22T16:20:00+08:00", "timezone": "Asia/Shanghai"}`，
**不是字符串**。直接 `.replace("Z", "+00:00")` 会抛出 `AttributeError`。
修复：判断类型后再提取 `datetime` 字段。

### 对下游脚本输出格式的脆弱耦合
`morning_reminder.py` 通过**正则解析文本输出**获取数据，不直接调 API。

| 依赖脚本 | 输出格式 | 耦合风险 |
|---------|---------|---------|
| `list_events.py` | `📅 MM/DD 日程` + `  MM/DD HH:MM ~ MM/DD HH:MM  标题` | 格式变 → 日程解析失败 |
| `list_tasks.py` | `📋 待办 (N 项)` + `  ○ 标题  截止 MM/DD` | 格式变 → 待办解析失败 |

如下游脚本输出格式变更，优先改为直接调 lark-cli 获取结构化 JSON，而非继续维护脆弱的正则解析。

## 触发条件

| 用户说 | 说明 |
|--------|------|
| 「晨间提醒」「早上提醒」「每日提醒」 | 手动触发 |
| cron 自动触发 | 每日 07:30 |

## 速查

```bash
python3 ~/.hermes/skills/morning-reminder/scripts/morning_reminder.py
```

## 输出格式

```markdown
📌 YYYY-MM-DD 星期X

☀️ 今日日程
  HH:MM 事件标题
  （暂无安排 🎉）

📋 逾期/今日截止
  ⚠️ 任务A  逾期N天
  ○ 任务B  截止 MM/DD 周X
  （今日无截止 🎉）          ← 有 urgent 无内容时
  （全部完成 🎉）            ← 全部无内容时

📋 后续待办                  ← 所有未逾期且非今日截止的待办
  ○ 任务C  截止 MM/DD 周X
  （暂无）

📅 明日日程（N项）
  HH:MM 事件A
  （暂无预告 🎉）
```

> ⚠️ `逾期/今日截止` 与 `后续待办` 是互斥分区。前者只收拢**逾期+今日截止**任务；后者收拢**未来截止**任务。两区独立输出，避免重复展示。

> 首行由 Python `datetime.strftime("%Y-%m-%d")` + `weekday()` 计算得出

| 模块 | 内容规则 |
|------|---------|
| 今日日程 | 全部事件，时间线排列 |
| 逾期/今日截止 | **截止今天 或 已逾期**（不含未来截止的任务），逾期加 ⚠️ 前缀并显示天数 |
| 后续待办 | 未来截止的所有未完成任务，独立归类不干扰焦点 |
| 明日预告 | 前3条 + 总数 |

## 使用流程

```
skill_view(name='morning-reminder')
  → 执行 morning_reminder.py
    → feishu-calendar list_events.py（今日 + 明日）
    → feishu-task list_tasks.py（全部待办）
    → 过滤 + 排序 + 合并输出
```

## 依赖脚本

| 脚本 | 路径 |
|------|------|
| 日历查询 | `~/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py` |
| 任务查询 | `~/.hermes/skills/productivity/feishu-task/scripts/list_tasks.py` |
| 角色编排 | `~/.hermes/skills/personal-os-roles/SKILL.md` |

## 内部实现要点

- **逾期检测**：构造 `今年到期日` 和 `明年到期日`，选离今天最近的已过期日期
  ```python
  due_this_year = datetime(today.year, due_month, due_day).date()
  due_next_year = datetime(today.year + 1, due_month, due_day).date()
  overdue_days = (today - min(d for d in [due_this_year, due_next_year] if d < today)).days
  ```
- **任务解析**：通过正则从 `list_tasks.py` 文本输出提取标题和截止日期
- **日历解析**：通过正则从 `list_events.py` 文本输出提取 `HH:MM 标题`

## 三角色输出

脚本会额外输出 `🧭 三角色行动建议`：

- 产品经理：根据 AgentOS 主线 YAML v2 做注意力收口，默认只展开 1-2 件今天真正要推进的事。
- 数据管家：汇总今日日程、逾期/今日截止、后续待办、明日预告的事实数量。
- 输入/记忆事实：只读展示微信读书本月阅读统计和 ima 最近笔记标题。
- AI执行官：给出最多 1-3 个核心任务。
- 伪忙碌提醒：当任务无法映射到主线，或十堰黑客松/外围事务挤占核心主线时提醒收敛。

## 可靠性护栏

- 日程和任务是事实；主线选择和伪忙碌判断是推断，输出必须区分。
- 飞书子脚本超过 25 秒或执行失败时，按空数据降级，并显示数据质量提醒。
- 没有关键词证据时不强行归类为任一主线，输出“今日主线不明确”。
- AI 执行官最多输出 1-3 个核心任务。
- 未接入的数据源（健康、睡眠、财务、微信聊天记录）不得出现在事实摘要里。
- 微信读书和 ima 只读接入；晨间提醒不写入 ima、不修改微信读书数据。

## 图片文字识别（OCR）备选

### `vision_analyze` 本地路径全部失败，tesseract 是唯一可靠备选

| 路径格式 | 结果 | 原因 |
|---------|------|------|
| `/absolute/path` (绝对路径) | ❌ 400 `unknown variant image_url` | 工具对本地路径有解析问题 |
| `file:///absolute/path` | ❌ 400 `unknown variant image_url` | API 不接受 file:// 协议 |
| `http://localhost:18080/image.jpg` | ❌ 400 `Invalid image source` | API 不接受 localhost URL |
| `https://public-url/image.jpg` | ✅ 需外网暴露 | 可行但不便 |

**结论**：所有本地路径方案在 MiniMax-M2 上均失败，tesseract 是唯一可靠备选，无需尝试其他路径格式。

### ffmpeg 缩放对 vision_analyze 无帮助

缩放后再调用 vision_analyze 仍报 `unknown variant image_url`，说明问题在路径解析层，不在图片体积。缩放仅在图片本身损坏（如 JFIF 头缺失）时有帮助。`file` 命令可验证图片格式正常：
```bash
file /path/to/image.jpg  # 输出 "JPEG image data" 即正常
```

```bash
tesseract /path/to/image.jpg stdout -l chi_sim+eng 2>/dev/null | head -80
```

详见 `references/ocr-fallback.md`。

## AgentOS Attention Governance

Morning output should use AgentOS attention language:

- 今天真正要推进的
- 先别掉线的
- 先攒着的
- 等反馈的
- 已经交给别人处理的

Do not expose `now/next/later/paused` to the user. Default to 1-2 committed items, at most 3 with a clear reason.
