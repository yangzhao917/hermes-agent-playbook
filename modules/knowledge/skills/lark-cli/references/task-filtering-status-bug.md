# Task Filtering Status Bug (2026-05-19 实测)

## 现象

调用 `tasks list` 时使用 `completed_status: not_started` 过滤，返回结果中同时包含：
- `status: "done"` 的已完成任务（47条）
- `status: "todo"` 的真正未完成任务（3条）

总计 50 条，has_more: true。

## 根因

飞书任务 API 的 `completed_status` 参数过滤逻辑依赖 `agent_task_status` 字段，而非 `status` 字段。

- `agent_task_status: 4` = 已完成（对应 status: done）
- `agent_task_status: 1` = 未完成（对应 status: todo）

当通过 `+complete` 或 `tasks patch` 标记任务完成时，`status` 变为 `"done"` 且 `completed_at` 被设置，但 `agent_task_status` 可能未同步更新，导致 `not_started` 过滤仍命中。

## 验证方法

```python
from datetime import datetime, timezone, timedelta
sh_tz = timezone(timedelta(hours=8))
now = datetime(2026, 5, 19, tzinfo=sh_tz)

for t in items:
    status = t.get('status', '')  # 'todo' = 未完成, 'done' = 已完成
    name = t.get('summary', '')
    due_ts = t.get('due', {}).get('timestamp', '0')
    due_dt = datetime.fromtimestamp(int(due_ts)/1000, tz=sh_tz) if due_ts and due_ts != '0' else None
    is_overdue = due_dt and due_dt < now

    if status == 'todo':
        print(f'[TODO] {name} | due: {due_dt}')
    elif status == 'done' and is_overdue:
        print(f'[DONE-overdue] {name} | (已过期但 status=done)')  # API bug 产物
```

## 正确判断"真正未完成"任务的方式

```python
# ✅ 正确：只看 status 字段
todo_tasks = [t for t in items if t.get('status') == 'todo']

# ❌ 错误：依赖 completed_status 过滤参数
# not_started 结果里也会有 status=done 的任务
```

## 2026-05-19 实测结果

| 分类 | 数量 |
|------|------|
| status=done（已完成，含过期） | 47 |
| status=todo（真正未完成） | 3 |
| 总计 | 50 |

真正未完成的 3 条 status=todo 任务：
- IF.Land AI Hackathon 校内赛 🎪 (2026-06-05)
- 交付Hermes日程管理给卢佩健 💰100 (2026-05-24)
- 哈尔滨复赛聚餐垫付700元 💰 (无期限)
