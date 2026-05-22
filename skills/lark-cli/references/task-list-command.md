# 飞书任务列表查询（正确方式）

## 查询未完成任务

```bash
lark-cli task tasks list --params '{"completed": false, "page_size": 50}' --format json
```

## 查询已完成任务

```bash
lark-cli task tasks list --params '{"completed": true, "page_size": 50}' --format json
```

## Python 解析模板

```python
import json, sys, datetime
from datetime import timezone, timedelta

sh_tz = timezone(timedelta(hours=8))
d = json.load(sys.stdin)
tasks = d.get('data', {}).get('items', [])

for t in tasks:
    summary = t.get('summary', '')
    status = t.get('status', '')  # 'todo' = 未完成, 'done' = 已完成
    due = t.get('due', {})
    due_ts = due.get('timestamp', '0') if due else '0'
    due_str = (
        datetime.datetime.fromtimestamp(int(due_ts)/1000, tz=sh_tz).strftime('%m/%d')
        if due_ts and due_ts != '0' else '无期限'
    )
    print(f'  [{status}] {summary} | 截止:{due_str}')
```

## 错误命令（不要用）

| 错误命令 | 问题 |
|---------|------|
| `lark-cli task +list` | `+list` 不是合法子命令，返回 unknown_subcommand error |
| `lark-cli task +get-my-tasks --complete false` | `--complete false` 语法不生效，需用 `tasks list` |

## 关键区别

- `tasks list --params '{"completed": false}'` → 布尔值过滤，返回纯未完成
- `+get-my-tasks` → 返回所有任务（已完成+未完成混杂），不支持完成状态过滤
