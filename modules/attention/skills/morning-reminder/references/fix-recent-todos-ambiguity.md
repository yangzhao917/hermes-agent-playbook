# Morning Reminder Skill 修复记录

## 问题描述

2026-05-27：用户反馈"今日待办展示的近期的待办，有歧义"。

需要修改 `format_today_todos()` 函数中对"近期"的定义或展示方式，避免与"今日截止"混淆。

## 修复方案

**待修复**（本次会话未执行）：修改 `morning_reminder.py` 中对近期任务的展示逻辑，区分"今日截止"和"近期"的时间范围定义。

## 代码位置

`~/.hermes/skills/morning-reminder/scripts/morning_reminder.py`

## 相关函数

- `format_today_todos()`: 展示今日截止任务
- `format_future_todos()`: 展示近期任务
- `get_weekday_label()`: 给日期加星期标签
- `fmt_due()`: 日期格式化 `MM/DD 周X`

## 修复方向

把"近期待办"的"近期"改成更明确的措辞（如"7日内"），或调整展示顺序让"今日截止"更醒目。