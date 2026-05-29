# feishu-task API 字段差异速查

## `+get-my-tasks` vs `tasks list`

| 属性 | `+get-my-tasks` | `tasks list` |
|------|----------------|-------------|
| 命令 | `lark-cli task +get-my-tasks` | `lark-cli task tasks list` |
| due 字段 | `due_at` (ISO string) | `due.timestamp` (毫秒) |
| status 字段 | `null` 表示未完成 | `"todo"` 表示未完成 |
| 成功判断 | `{"ok": true}` | `{"code": 0}` |

## 关键坑点

### 1. 成功响应格式不同
```python
# tasks list → code=0 表示成功
if data.get("code") != 0:
    print(f"API error: {data}")

# +complete/+create/+reopen → ok=true 表示成功
if not data.get("ok"):
    print(f"Command failed: {data}")
```

### 2. due 字段格式不同
```python
# +get-my-tasks 返回 ISO 字符串
due_at = item.get("due_at")  # "2026-05-28T08:00:00+08:00"

# tasks list 返回毫秒时间戳
due_ts = item.get("due", {}).get("timestamp")  # 毫秒，1748400000000
```

### 3. status 标记方式不同
```python
# +get-my-tasks: null = 未完成
status = item.get("status")  # None = todo, 有值 = done

# tasks list: "todo" = 未完成
status = item.get("status")  # "todo" = todo, "done" = done
```

## 修改截止时间的正确方式

```bash
# 使用 +update（推荐），支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
lark-cli task +update --task-id "<guid>" --due "2026-05-25 20:00:00"

# tasks list 的 due.timestamp 是毫秒，不能直接用于 +create 的 --due
# lark-cli 会自动转换，无需手动处理
```