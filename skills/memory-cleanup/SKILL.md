---
name: memory-cleanup
description: "Use when asked to clean up or reduce memory entries, or when MEMORY.md is getting bloated. Automatically removes version-number references, one-week-old one-time events, and exact duplicates."
version: 1.0.0
author: 杨钊
license: MIT
metadata:
  hermes:
    tags: [memory, cleanup, housekeeping, dedup]
---

# memory-cleanup

自动清理 `~/.hermes/memories/MEMORY.md` 中的过期/冗余条目。

## 何时使用

- 用户说"清理记忆"、"清理 memory"
- `MEMORY.md` 超过 20 条时考虑运行
- 用户说"把过期的东西删掉"

## 清理规则

| 类型 | 条件 | 动作 |
|------|------|------|
| 版本号引用 | 含 `v1.2.3`、`CLI 1.0` 等版本号 | 删除 |
| 过期一次性事件 | 日期超过 1 周且含"一次性" | 删除 |
| 精确重复 | 完全相同的连续条目 | 保留第一个 |

**不删除**：用户偏好、持久环境事实、跨 session 仍然有效的上下文。

## 使用方式

```bash
# 预览（不实际删除）
python3 ~/.hermes/skills/memory-cleanup/scripts/memory_cleanup.py --dry-run

# 执行清理
python3 ~/.hermes/skills/memory-cleanup/scripts/memory_cleanup.py
```

## 日志

运行日志位于 `~/.hermes/logs/memory_cleanup.jsonl`（JSON Lines 格式）。

状态枚举：
- `heartbeat` — 无记忆条目时的心跳
- `clean` — 有条目但无需清理
- `cleaned` — 实际清理了条目

## 验证

```bash
python3 ~/.hermes/skills/memory-cleanup/scripts/memory_cleanup.py --dry-run
# 确认删除条目预览无误后再执行
```
