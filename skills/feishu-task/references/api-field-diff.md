# feishu-task API 字段差异速查（2026-05-22 实测）

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

# +complete/+create → ok=true 表示成功
if not data.get("ok"):
    print(f"API error: {data}")
```

### 2. due_at vs due.timestamp
```python
# +get-my-tasks — ISO string
due_at = t.get("due_at")  # "2026-05-22T00:00:00+08:00"
dt = datetime.fromisoformat(due_at[:19]).replace(tzinfo=SH_TZ)

# tasks list — 毫秒时间戳
due_ts = t.get("due", {}).get("timestamp", "0")  # "1779465600000"
dt = datetime.fromtimestamp(int(due_ts) / 1000, tz=SH_TZ)
```

### 3. 批量完成必须串行
禁止并行，必须每次单独 `--task-id`：
```bash
lark-cli task +complete --task-id <guid1>
lark-cli task +complete --task-id <guid2>
```

### 4. page_size 上限 100
```bash
lark-cli task tasks list --params '{"page_size": 100}'
```

### 5. 用户 open_id
```
ou_5b875f5ec5752b06832bb240ad482ec0
```
