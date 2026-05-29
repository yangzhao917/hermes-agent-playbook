---
name: feishu-calendar
description: 飞书日程管理（查看/创建/修改/删除/忙闲查询）
version: 1.0.0
category: productivity
tags: [feishu, calendar, schedule, agenda]
---

# feishu-calendar 📅

> ⚠️ **禁区**
> - 时间戳必须用 Python 计算，禁止手算
> - `events patch/delete` 必须用 `--params` JSON，禁止位置参数
> - 日历时间戳是**秒级**，任务时间戳是毫秒级（两个模块不同）
> - **`instance_view --format json` 输出多行格式化 JSON**，禁止逐行解析，必须先 `json.loads(whole_output)` 再 fallback
> - **脚本路径是 `productivity/feishu-calendar/scripts/`**，不是 `feishu-calendar/scripts/`（注意中间多了 `productivity/` 这一层）

> **⚠️ 路径陷阱**：脚本实际位于 `~/.hermes/skills/productivity/feishu-calendar/scripts/`，SKILL 里所有速查命令均已正确使用此路径。但若见到其他路径写法（`feishu-calendar/scripts/`、`productivity/feishu-calendar/`），均视为已废弃，勿用。

## ⚠️ 陷阱与已知问题

### 响应包装格式
`lark-cli calendar +agenda --format json` 返回 `{"ok": true, "data": [...]}`，不是裸数组。解析必须取 `data["data"]`。**但 `+agenda` 不加 `--format json` 时直接输出人类可读文本**（包含腾讯会议链接），无需解析 JSON。

### `start_time` / `end_time` 是嵌套对象
事件中的 `start_time` 是 `{"datetime": "...", "timezone": "..."}`，不是字符串。解析时需判断类型。

### 日历 ID 大小写敏感
文件夹名为 `HermesAgent`（大写 H），不是 `hermesAgent`。

## ⚠️ 使用流程（必须遵循）

**每次执行飞书日历操作前，必须先加载本技能，再执行脚本。**

```
正确流程：skill_view(name='feishu-calendar') → 读速查 → 执行脚本
错误流程：直接调脚本（跳过 skill_view）
```

禁止凭记忆直接敲命令或直接调用脚本。每次都要先加载 skill 确认命令和参数。

## 触发条件

用户说「查日历」「看看今天」「明天有什么安排」「本周日程」「创建日程」「修改日程」「删除飞书日程」「几点有空」

## 速查

| 操作 | 命令 |
|------|------|
| 查今日 | `lark-cli calendar +agenda` |
| 查指定日 | `lark-cli calendar +agenda`（默认当天，输出 JSON 可用 `--format json`） |
| 脚本查今日 | `python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py --today` |
| 脚本查明日 | `python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py --tomorrow` |
| 脚本查指定日 | `python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py --date 2026-05-25` |
| 脚本查日期范围 | `python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py --start 2026-05-20 --end 2026-06-05` |
| 创建日程 | `python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/create_event.py --summary "产品评审" --start "2026-05-25T14:00" --end "2026-05-25T15:00"` |
| 修改日程 | `python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/patch_event.py --event-id <id> [--summary "新标题"] [--start "..."] [--end "..."] [--description "..."]` |
| 删除日程 | `python3 ~/.hermes/skills/feishu-calendar/scripts/delete_event.py --event-id <id> [--yes]` |
| 查询忙闲 | `python3 ~/.hermes/skills/feishu-calendar/scripts/freebusy.py --user-id ou_5b875f5ec5752b06832bb240ad482ec0 --start "2026-05-25T00:00:00+08:00" --end "2026-05-25T23:59:59+08:00"` |

## 输出格式（被 morning-reminder 依赖，禁止随意变更）

`list_events.py` 输出格式为半公开 API：

```
📅 MM/DD 日程
  MM/DD HH:MM ~ MM/DD HH:MM  标题
  （暂无安排 🎉）
```

> 第一行为标题行（含日期），后续行为事件行。如需修改格式，请同步通知 morning-reminder 维护者。

### 搜索日程（search_event）
`search_event` 需要 `calendar_id` 同时作为**位置参数**（路径）和 `--params` JSON（API 调用），`query` 放在 `--data` JSON 里：

```bash
/usr/lib/node_modules/@larksuite/cli/bin/lark-cli calendar events search_event \
  "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn" \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn"}' \
  --data '{"query":"CSS播客"}'
```

⚠️ **常见错误**：仅传位置参数、或仅把 `calendar_id` 放在 `--data` 里，都会报 `missing required path parameter: calendar_id` 或 `query is required`。必须同时使用位置参数 + `--params` + `--data`。

文档内容较长时（~200行 Markdown），`+update --mode overwrite` 会触发 BLOCKED 超时。
**修复**：改用 `lark-cli docs +fetch` 先读取现有内容，再通过分段写入，或直接重建文档。

`create_event.py` 是简化封装，**不支持** `--description` 和 `--attendee-ids`。若需要这些参数，直接用 lark-cli：

```bash
lark-cli calendar +create \
  --summary "日程标题" \
  --start "2026-06-12T18:00" \
  --end "2026-06-14T17:50" \
  --description "详细描述，含地点、交通、链接等" \
  --calendar-id "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn"
```

## 完整示例

```bash
# 查看今日日程
python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py --today
# 查看本周范围日程
python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/list_events.py --start 2026-05-25 --end 2026-05-31

# 创建日程（脚本，仅标题+时间）
python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/create_event.py \
  --summary "周会" \
  --start "2026-05-26T10:00" \
  --end "2026-05-26T11:00"

# 创建日程（lark-cli，支持 description + attendee）
lark-cli calendar +create \
  --summary "浦软黑客松 AINX 2026" \
  --start "2026-06-12T18:00" \
  --end "2026-06-14T17:50" \
  --description "📍 地址：上海市浦东新区郭守敬路498号2号楼" \
  --calendar-id "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn"

# 修改日程标题
python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/patch_event.py \
  --event-id "d721c65a-7995-495f-a838-18cb496f5226_0" \
  --summary "新周会名称"

# 删除日程
python3 ~/.hermes/skills/productivity/feishu-calendar/scripts/delete_event.py \
  --event-id "d721c65a-7995-495f-a838-18cb496f5226_0" --yes
```

## 个人日历 ID

```
feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn
```

## API 限制与分段处理

| 限制项 | 上限 | 处理方式 |
|--------|------|---------|
| `instance_view` 单次时间跨度 | 40 天 | 脚本自动拆分为 ≤35 天多段查询 |
| `instance_view` 单次返回条数 | 1000 条 | 脚本自动再拆分，用户无感知 |

## 时间格式

- `--start/--end`（创建/修改）：ISO 8601
  - `2026-05-25T14:00`（当天 14:00）
  - `2026-05-25T14:00+08:00`（带时区）
- 内部计算：秒级 Unix 时间戳

## 内部实现说明

- `list_events.py` 内置 **40 天分段查询**，无需外部处理
- 所有脚本使用**两层 JSON 解析**（整段优先 + 逐行 fallback），兼容多行格式化 JSON 和含 `[deprecated]` 前缀的输出
