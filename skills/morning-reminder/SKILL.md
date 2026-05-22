---
name: morning-reminder
description: "Use when setting up or checking daily calendar reminders. Queries Feishu calendar and formats today's and tomorrow's agenda."
version: 1.0.1
author: 杨钊
license: MIT
metadata:
  hermes:
    tags: [calendar, feishu, reminder, daily, agenda]
    requires_toolsets: [terminal]
---

# morning-reminder

每日推送飞书日历日程摘要（今日 + 明日）。

## 触发规则

- 用户说"设置晨间提醒"、"每天早上看日历"
- cron job 自动触发
- 加载本 skill 后调用对应脚本，不要自己拼接命令

## 速查

| 操作 | 命令 |
|------|------|
| 拉取今日+明日日历 | `python3 ~/.hermes/skills/morning-reminder/scripts/morning_reminder.py` |
| 日历 API | `lark-cli calendar +agenda`（秒级时间戳，不用 datetime 格式） |

## 使用方式

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
