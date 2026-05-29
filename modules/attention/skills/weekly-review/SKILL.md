---
name: weekly-review
description: 每周复盘总结（本周事实 + 下周取舍，生成飞书文档 + 微信摘要）
version: 2.0.0
category: productivity
tags: [feishu, review, weekly, attention, agentos]
---

# weekly-review

每周复盘不是报表，也不是单纯计划。它的产品定义是：

```text
周复盘 = 本周事实 + 下周取舍
```

## Output

- 微信：本周真正推进了、下周建议只抓、先不用花力气、需要确认。
- 飞书：完整事实、证据、阶段进展、数据质量和不确定部分。

## Commands

```bash
python3 ~/.hermes/scripts/weekly_review.py
python3 ~/.hermes/scripts/weekly_review.py --week-start 2026-05-25
python3 ~/.hermes/scripts/weekly_review.py --check-path
```

## Guardrails

- Use daily review docs as the fact source.
- Do not invent health, sleep, finance, or WeChat chat data.
- Generate mode/stage suggestions only; do not execute high-impact changes automatically.
- Keep facts, inferences, and uncertainties distinct.
