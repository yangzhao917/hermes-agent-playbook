# 飞书任务列表过滤（2026-05-19 实测）

## 两个 API 的本质区别

| API | 命令 | 过滤能力 |
|-----|------|---------|
| `/task/v2/tasks`（get-my-tasks） | `lark-cli task +get-my-tasks` | ❌ 无 completed_status 参数，返回所有任务 |
| `/task/v2/tasks/list` | `lark-cli task tasks list` | ✅ 支持 `completed_status` 参数 |

## `task tasks list` 参数

```json
{
  "completed_status": "done",       // 已完成
  "completed_status": "not_started", // 未完成
  "page_size": 50,
  "page_token": ""                   // 分页
}
```

## 完整解析脚本（查未完成任务）

```bash
lark-cli task tasks list \
  --params '{"completed_status": "not_started", "page_size": 50}' \
  --format json 2>&1 | python3 -c "
import json, sys
from datetime import datetime, timezone, timedelta
sh_tz = timezone(timedelta(hours=8))
data = json.loads(sys.stdin.read())
items = data.get('data', {}).get('items', [])
has_more = data.get('data', {}).get('has_more', False)
print(f'未完成任务: {len(items)}, has_more: {has_more}')
for t in items:
    name = t.get('summary', '')
    due = t.get('due_at', '')
    due_str = datetime.fromisoformat(due[:19]).strftime('%Y-%m-%d') if due else '无期限'
    print(f'  {name} | {due_str}')
"
```

## 验证批量完成是否成功

`lark-cli task +complete --task-id <guid>` 返回 `{"ok": true}` 后，**不要**用 `get-my-tasks` 验证（它显示全部56条）。正确做法：

```bash
lark-cli task tasks list \
  --params '{"completed_status": "done", "page_size": 50}' \
  --format json 2>&1 | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
items = data.get('data', {}).get('items', [])
has_more = data.get('data', {}).get('has_more', False)
print(f'已完成: {len(items)}, has_more: {has_more}')
for t in items:
    name = t.get('summary', '')
    ct = t.get('completed_at', 0)
    if ct:
        from datetime import datetime, timezone, timedelta
        sh_tz = timezone(timedelta(hours=8))
        dt = datetime.fromtimestamp(ct, tz=sh_tz)
        print(f'  {name} | 完成于 {dt.strftime(\"%Y-%m-%d %H:%M\")}')
"
```

## completed_at 时间戳

飞书返回的 `completed_at` 是**毫秒级**时间戳（如 `1779143758000`），需除以 1000 才能用于 `datetime.fromtimestamp()`。但更简单的方法是直接用 `tasks list --format json` 解析时按原样传给 datetime：
```python
datetime.fromtimestamp(int(str(ct)[:10]), tz=sh_tz)  # 取前10位（秒）
```
