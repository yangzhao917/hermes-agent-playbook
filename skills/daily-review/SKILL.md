---
name: daily-review
description: "Use when setting up or running a daily review workflow. Generates a structured review document in Feishu Docs, idempotent (updates existing doc by date)."
version: 1.0.0
author: 杨钊
license: MIT
metadata:
  hermes:
    tags: [feishu, review, daily, document, docs, idempotent]
    requires_toolsets: [terminal]
---

# daily-review

每日 23:30 自动生成复盘总结文档，写入飞书 `hermesAgent/每日复盘/` 文件夹。

## 何时使用

- 用户说"设置每日复盘"、"每天自动生成复盘"
- cron job 自动触发

## 幂等性

- **文档已存在**（当天已运行过）→ 覆盖内容，保留文档链接
- **文档不存在** → 创建新文档
- 每天只会有一条文档，文件名含日期

## 使用方式

```bash
python3 ~/.hermes/skills/daily-review/scripts/daily_review.py
```

## 文档结构

```
# YYYY-MM-DD 复盘总结

## 📋 今日计划
来源：昨日「明日待办」+ 今日新增计划

| 时间 | 事项 | 备注 |

## ✅ 今日完成

| 完成 | 未完成 | 调整 |

## ⏰ 明日待办

| 时间 | 事项 | 备注 |

## 📌 待跟进
🔴 紧急  🟡 一般  🟢 缓办

## 📅 后续安排

| 日期 | 事项 |

## 💡 今日收获

## ⚡ 今日感受
```

## 验证

```bash
python3 ~/.hermes/skills/daily-review/scripts/daily_review.py
# 应在飞书创建或更新当天复盘文档
```
