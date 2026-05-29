# Calendar Query by Range (instance_view)

## 标准模式

`lark-cli` 没有 `calendar events list` 命令。按时间范围查日程的唯一方式是 `instance_view` + Python 动态计算 Unix 时间戳。

## 计算函数

```python
from datetime import datetime, timezone, timedelta

def get_ts_range(year, month, day, end_day=None, sh_tz=timezone(timedelta(hours=8))):
    """返回 (start_ts, end_ts) Unix timestamps"""
    start = datetime(year, month, day, 0, 0, 0, tzinfo=sh_tz)
    end_day = end_day or day
    end = datetime(year, month, end_day, 23, 59, 59, tzinfo=sh_tz)
    return int(start.timestamp()), int(end.timestamp())
```

## 常用范围

| 范围 | 代码 |
|------|------|
| 今天 | `get_ts_range(2026, 5, 19)` |
| 本周（周一~周日） | `get_ts_range(2026, 5, 18, 24)` |
| 近一周 | `datetime.now(sh_tz) - timedelta(days=7)` 开始 |
| 本月 | `get_ts_range(2026, 5, 1, 31)` |

## 完整示例：本周日程

```python
from datetime import datetime, timezone, timedelta
import subprocess, json

sh_tz = timezone(timedelta(hours=8))
start = datetime(2026, 5, 18, 0, 0, 0, tzinfo=sh_tz)
end = datetime(2026, 5, 24, 23, 59, 59, tzinfo=sh_tz)

ts_start = int(start.timestamp())
ts_end = int(end.timestamp())

result = subprocess.run(
    ["lark-cli", "calendar", "events", "instance_view",
     "--params", json.dumps({
         "calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn",
         "start_time": str(ts_start),
         "end_time": str(ts_end)
     }),
     "--format", "json"],
    capture_output=True, text=True, timeout=20
)

data = json.loads(result.stdout)
for e in sorted(data.get('data', {}).get('items', []), key=lambda x: x['start_time']['timestamp']):
    dt = datetime.fromtimestamp(int(e['start_time']['timestamp']), tz=sh_tz)
    print(f"{dt.strftime('%m/%d %H:%M')} | {e.get('summary', '(无标题)')}")
```

## 查指定日期的日程

```python
# 2026-05-19 整天
ts_start = int(datetime(2026, 5, 19, 0, 0, 0, tzinfo=sh_tz).timestamp())
ts_end = int(datetime(2026, 5, 19, 23, 59, 59, tzinfo=sh_tz).timestamp())
```

## 踩坑记录

| 日期 | 手算 ts | 实际 | 错误原因 |
|------|---------|------|---------|
| 2026-05-19 00:00 CST | 1779206400 | 1779120000 | May 20 不是 May 19！CST 00:00 = UTC 前一天 16:00 |
| 2026-05-18 21:00 CST | 1779109200 | — | ✅ 已验证正确 |

**结论：永远不要手算时间戳。** Python 两行搞定。

## ⚠️ 严重 bug：instance_view 范围查询返回 0（事件实际存在）

**问题**（2026-05-20 实测）：传正确的 `start_time`/`end_time`（Python 计算的 2026-05-19 整天 ts = `1779120000` ~ `1779206400`），`instance_view` 返回 0 条目。但直接用 `events get` + event_id 能查到事件。

**排查结果**：
- `instance_view` + 正确时间范围：❌ 0 条目
- `search_event` + keywords：❌ 0 条目
- 直接 curl 飞书 API `instance_view`：❌ 0 条目
- 数字 calendar_id (`7426768448349241347`) vs 字符串格式：❌ 同样 0
- **直接 `events get` + event_id**：✅ 成功

**结论**：`instance_view` 接口对单事件非重复日程的查询有 bug。**但 `+agenda` 最稳定：**

```bash
# ✅ 最稳定：+agenda（自动处理时区，支持 ISO 时间）
lark-cli calendar +agenda \
  --calendar-id "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn" \
  --start "2026-05-19T00:00:00+08:00" \
  --end "2026-05-19T23:59:59+08:00"

# ✅ 已知事件 ID 时：直接 get
lark-cli calendar events get \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn", "event_id": "d721c65a-7995-495f-a838-18cb496f5226_0"}'

# ❌ 不稳定：range 查询（instance_view）
lark-cli calendar events instance_view \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn", "start_time": "1779120000", "end_time": "1779206400"}'
```

**推荐顺序**：`+agenda`（尝试）→ `instance_view`（即使0结果也可能是正确的）→ 如果两者都0，用任务系统交叉验证。

**2026-05-21 新发现：`+agenda` 本身也可能返回 0** — 即使在完整日期范围内使用，`+agenda` 仍可能返回 "No calendar events"。此时需结合任务系统（`tasks list --completed true`，按 completed_at 过滤）交叉验证。如果任务系统显示当天有完成记录，说明日历和任务是两个独立系统——用户没有在日历上建日程，但有任务记录（如18:30完成某任务）。

**已知事件 ID**（澄澈少年日历）：
| 事件 | event_id |
|------|----------|
| 过道对白 节目访谈录制 | `d721c65a-7995-495f-a838-18cb496f5226_0` |
