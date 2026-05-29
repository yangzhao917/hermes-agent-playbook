---
name: daily-review
description: 每日复盘总结（微信注意力收口 + 飞书事实档案）
version: 3.0.0
category: productivity
tags: [feishu, review, daily, attention, agentos]
---

# daily-review

每日 23:30 自动生成复盘总结：

- 微信：注意力收口、明天建议、需要确认的纠偏入口。
- 飞书：事实档案和可追溯复盘记录。

## Core Principle

旧模型是日程/任务/信息总结；新模型是注意力收口。

微信第一屏只回答：

- 今天真正推进了什么
- 明天建议只抓什么
- 先不用花力气的事
- 需要确认/纠偏
- 我不确定的部分

## Commands

```bash
python3 ~/.hermes/scripts/daily_review.py
python3 ~/.hermes/scripts/daily_review.py --date 2026-05-22
python3 ~/.hermes/scripts/daily_review.py --check-path
```

## Data Sources

- Feishu tasks and calendar are facts.
- WeRead and ima are read-only input facts.
- Attention classification and busywork diagnosis are inferences.

## Guardrails

- Separate facts, inferences, and uncertainties.
- Do not invent unavailable health, sleep, finance, or WeChat chat data.
- Keyword matches are candidate evidence only.
- Daily review does not automatically write long-term memory.
- High-impact corrections require confirmation.
