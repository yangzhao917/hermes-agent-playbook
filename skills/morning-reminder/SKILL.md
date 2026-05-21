---
name: morning-reminder
description: "Use when setting up or checking daily calendar reminders. Queries Feishu calendar and formats today's and tomorrow's agenda."
version: 1.0.0
author: 杨钊
license: MIT
metadata:
  hermes:
    tags: [calendar, feishu, reminder, daily, agenda]
    requires_toolsets: [terminal]
---

# morning-reminder

每日推送飞书日历日程摘要（今日 + 明日）。

## 何时使用

- 用户说"设置晨间提醒"、"每天早上看日历"
- cron job 自动触发

## 使用方式

依赖 `lark-cli`。查询飞书日历并格式化输出：

```bash
python3 ~/.hermes/skills/morning-reminder/scripts/morning_reminder.py
```

## 输出格式

```
☀️ 今日日程
  HH:MM 事件标题
  或: 暂无安排 🎉

📅 明日日程（你可能更关心这个）
  HH:MM 事件标题
  或: 暂无安排 🎉
```

## 验证

```bash
python3 ~/.hermes/skills/morning-reminder/scripts/morning_reminder.py
# 应输出今日+明日日历事件，或"暂无安排"
```
