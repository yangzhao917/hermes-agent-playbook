# feishu-task skill 字段差异速查（2026-05-22 官方实测）

## `+get-my-tasks` vs `tasks list` 完整对比

| 属性 | `+get-my-tasks` | `tasks list` |
|------|----------------|-------------|
| 命令 | `lark-cli task +get-my-tasks` | `lark-cli task tasks list` |
| 截止日期字段 | `due_at` ISO字符串 | `due.timestamp` 毫秒时间戳 |
| 状态字段 | `status: null`（不返回） | `status: "todo"` / `"done"` |
| 创建时间 | `created_at` ISO字符串 | `created_at` 毫秒时间戳 |
| 完成时间 | `completed_at` ISO/null | `completed_at` 毫秒时间戳（字符串） |
| 支持过滤 | ❌ 不支持 completed 过滤 | ✅ `completed: true/false` |
| 任务 ID | 只有 `guid` | `guid` + `task_id`（界面 ID） |
| 分页 | 无 | `--page-all`、`--page-token` |

## 时间戳解析

```python
# tasks list 的毫秒时间戳
ts = "1779356755000"
dt = datetime.fromtimestamp(int(ts)/1000, tz=sh_tz)

# +get-my-tasks 的 ISO 字符串
iso = "2026-05-22T02:38:26+08:00"
dt = datetime.fromisoformat(iso[:19]).replace(tzinfo=sh_tz)
```

## 成功返回格式（按命令分开）

| 命令 | 成功返回 |
|------|---------|
| `+complete` | `{"ok": true}` |
| `+reopen` | `{"ok": true}` |
| `+create` | `{"ok": true}` |
| `tasks list` | `{"ok": true}` |
| `+search` | `{"ok": true}` |
| `tasks delete` | `{"code": 0}` |
| `tasks patch` | `{"code": 0}` |

> ⚠️ 不要统一用 `code == 0` 判断，不同命令格式不同。
