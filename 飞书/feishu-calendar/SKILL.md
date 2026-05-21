---
name: feishu-calendar
description: 飞书日历管理 skill，基于 lark-cli 实现日程的查看、创建、删除。专注于可读性输出和时间便捷查询（--today/--week/--range）。当用户说「今天有什么安排」「查日历」「创建日程」「删除日程」时加载。
version: 1.0.0
category: productivity
---

## 依赖

- Python 3（虚拟环境）：`~/.hermes/hermes-agent/venv/bin/python3`
- 底层工具：`lark-cli`（必须先 `skill_view(name='lark-cli')` 确认命令语法）
- 无额外依赖包

## 脚本目录

```
/home/ubuntu/skills/feishu-calendar/scripts/
├── list_events.py    # 查看日程（--today/--tomorrow/--this-week/--next-week/--range）
├── get_event.py     # 查看单条日程详情
├── create_event.py  # 创建日程
└── delete_event.py  # 删除日程
```

## 调用方式

```bash
# 查看今天日程
/home/ubuntu/skills/feishu-calendar/scripts/list_events.py --today

# 查看本周日程
/home/ubuntu/skills/feishu-calendar/scripts/list_events.py --this-week

# 查看指定日期范围
/home/ubuntu/skills/feishu-calendar/scripts/list_events.py --range 2026-05-20 2026-05-25

# 查看单条日程详情
/home/ubuntu/skills/feishu-calendar/scripts/get_event.py --event-id <event_id>

# 创建日程
/home/ubuntu/skills/feishu-calendar/scripts/create_event.py --summary "标题" --start "2026-05-22T14:00" --end "2026-05-22T15:00"

/# 删除日程（需要 event_id）
/home/ubuntu/skills/feishu-calendar/scripts/delete_event.py --event-id <event_id>
```

## 设计原则

**只做展示层增强，不重复造轮子**。底层继续用 lark-cli，script 层只做格式化/日期解析/友好输出，不直接调飞书 API。

## 显示格式规范

**两条铁律：**

1. **日期显示具体日期**（如 `🔴 05/22`），禁止相对天数（`1天后`、`2天后`）
2. **输出必须人类可读**，不能只贴 raw 输出

正确格式：
- `🔴 05/22 14:00-15:00` — 今天
- `🟡 05/23 09:00` — 明天
- `📅 05/25 10:00` — 未来某天
- `⚠️ 05/20 14:00 (已取消)` — 已取消
- `⏸️ 05/20 14:00 (已结束)` — 已结束

## 用户信息

- 用户名：澄澈少年
- 个人日历 ID：`<CALENDAR_ID>`

## 时间戳计算规范

**所有日期/时间计算必须用 Python**，禁止手算：

```python
# 正确
from datetime import datetime, timezone, timedelta
sh_tz = timezone(timedelta(hours=8))
ts = int(datetime(2026, 5, 22, 14, 0, 0, tzinfo=sh_tz).timestamp())
# → 1779170400

# 错误：手算时间戳，容易跨月跨年出错
```

## lark-cli 版本记录

测试通过的版本：`lark-cli/1.0.33+`

## 相关技能

- `lark-cli`：底层飞书 CLI 工具，所有操作实际走这里
- `feishu-task`：飞书任务管理（已完成）
- `feishu`：飞书深度集成中枢（包含权限/协作/文档等高层逻辑）
