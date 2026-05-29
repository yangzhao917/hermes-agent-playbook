# lark-cli Schema 参数验证 (2026-05-20)

## task.tasks.list

| 参数 | 类型 | required | 说明 |
|------|------|----------|------|
| `completed` | boolean | ❌ | ✅ 正确过滤参数：`true`=已完成，`false`=未完成 |
| `agent_task_status` | integer | ❌ | 智能体任务状态细分（1-4） |
| `page_size` | integer | ❌ | 默认50 |
| `page_token` | string | ❌ | 分页标记 |
| `type` | string | ❌ | 只支持 `"my_tasks"` |

> ⚠️ `completed_status` 不是合法参数（字符串形式不生效，2026-05-20 实测）

## task +complete / +reopen

```
--task-id string  ✅ 正确
位置参数           ❌ 不支持
```

## task +search

```
--completed       flag（无值=查已完成）
--completed false flag with value（查未完成）
```

## task.tasks.patch update_fields 白名单

`summary`, `description`, `start`, `due`, `completed_at`, `extra`, `custom_complete`, `repeat_rule`, `mode`, `is_milestone`, `custom_fields`

> ⚠️ `status` 不在白名单，标记完成只能用 `+complete --task-id`

## calendar.events.instance_view

| 参数 | 类型 | required | 说明 |
|------|------|----------|------|
| `calendar_id` | string | ✅ | 日历 ID |
| `start_time` | string | ✅ | Unix 秒级时间戳 |
| `end_time` | string | ✅ | Unix 秒级时间戳 |
| `user_id_type` | string | ❌ | open_id/user_id/union_id |

## 时间戳精度

| 模块 | 字段 | 精度 |
|------|------|------|
| 日历 events patch | start_time.timestamp / end_time.timestamp | **秒级** |
| 任务 tasks list | due.timestamp | **毫秒级** |
| 任务 +create | --due | ISO 8601 字符串 |
