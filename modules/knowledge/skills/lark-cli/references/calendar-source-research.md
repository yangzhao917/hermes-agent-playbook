# lark-cli 日历模块知识点（2026-05-22 源码验证）

## 源码结构

```
shortcuts/calendar/
├── shortcuts.go         # Shortcuts() 注册所有命令
├── calendar_agenda.go  # +agenda
├── calendar_create.go  # +create
├── calendar_update.go  # +update
├── errors.go           # wrapPredefinedError（处理 190014 等）
└── helpers.go          # resolveStartEnd、rejectCalendarAutoBotFallback
```

## +agenda 内部机制

**底层调用 `instance_view` API**，并实现：
- **40天限制**：自动递归拆分为多个子窗口（每段 ≤ 35 天）
- **1000 条限制**：自动递归拆分更小窗口（最小 2 小时）
- **去重**：`event_id + start_timestamp + end_timestamp` 唯一键
- **过滤 cancelled**：状态为 `cancelled` 的日程自动过滤，不展示

```go
// 关键常量
maxInstanceViewSpanSeconds = 40 * 24 * 60 * 60  // 40天
minSplitWindowSeconds = 2 * 60 * 60             // 2小时（最小区间）
larkErrCalendarTimeRangeExceeded = 193103        // 范围超限 → 拆分
larkErrCalendarTooManyInstances = 193104         // 条数超限 → 拆分
```

## +create 内部机制（2-step + rollback）

1. **POST /events** 创建日程
2. **POST /events/{id}/attendees** 添加参与人
3. **失败时自动回滚**：删除已创建的日程

```go
// attendee ID 前缀强校验
ou_  → type: "user",    user_id
oc_  → type: "chat",   chat_id
omm_ → type: "resource", room_id
// 其他格式 → 报错：invalid attendee id format
```

## +update（多-step，不回滚）

1. `PATCH /events/{id}` 更新日程字段
2. `POST /events/{id}/attendees/batch_delete` 移除参与人
3. `POST /events/{id}/attendees` 添加参与人

**失败后继续执行其余步骤，不回滚**（与 +create 不同）

## start/end 时间解析

`common.ParseTime()` 接受多种格式：
- `2026-05-22` → 当天 00:00 +08:00
- `2026-05-22T14:00` → 当天 14:00
- `2026-05-22T14:00+08:00` → 带时区

**返回秒级 Unix 时间戳字符串**（`"1779170400"`），不是毫秒。

## is_all_day 处理（CLI 自动修正）

当 end_time 用 `date` 而非 `timestamp` 时（全天日程）：
- CLI 自动 `date - 1秒`，避免把结束日本身算进去
- e.g. `2026-05-25` 全天 → 实际为 `2026-05-24 23:59:59`

## 日历命令成功判断

**需要实测验证**（与 tasks 不同，calendar 命令尚未实测）：
- 预期：`{"code": 0}` 表示成功
- 建议：先用 `lark-cli calendar +agenda` 实测一次，记录真实响应格式

## 自动 bot fallback 陷阱

`rejectCalendarAutoBotFallback`：若身份自动降级为 bot，calendar 命令会操作 bot 日历而非用户日历。
- 正确做法：`lark-cli auth login --domain calendar` 重刷用户身份
- 或显式 `--as bot`（有意为之才用）

## 时间戳精度（任务 vs 日历）

| 模块 | 字段 | 精度 |
|------|------|------|
| 日历 | `start_time.timestamp` / `end_time.timestamp` | **秒级** |
| 任务 | `due.timestamp` | **毫秒级** |

**混用会导致日期错误**，两个模块必须分别处理。
