# 日历事件过滤：cancelled 事件与 null summary

**2026-05-22 发现**

## 问题现象

日历查询返回的事件中，有些事件的 `summary` 为 `null`，显示为"无标题"。这些事件实际上是**已取消**的事件。

```python
{
  "event_id": "97f6fac7-d4fb-4ac2-b7f8-1a3079df911d_0",
  "summary": None,
  "start_time": {"timestamp": "1747881600", "type": "timestamp"},
  "end_time": {"timestamp": "1747881900", "type": "timestamp"},
  "status": "cancelled"   # ← 关键字段
}
```

## 根因

飞书日历的 cancelled 事件不会从 API 返回中彻底消失，而是将 `status` 标记为 `"cancelled"`、`summary` 置为 `null`。这些记录仍然存在于返回的事件列表中。

## 正确处理

```python
def get_calendar_events(token, cal_id, date_str):
    events = api_call(...)
    result = []
    for ev in events:
        if ev.get("status") == "cancelled":
            continue                                          # ← 必须过滤
        t = format_event_time(ev)
        name = ev.get("summary") or "无标题"                  # ← fallback
        result.append((t, name))
    return result
```

## 教训

- **不要假设所有事件都有 summary**——cancelled 事件的 summary 是 `None`，不是空字符串
- **不要只看返回数量判断是否有内容**——cancelled 事件也会被计入返回数量
- **永远对 `status` 字段做过滤**，即使只想过滤已删除的事件
