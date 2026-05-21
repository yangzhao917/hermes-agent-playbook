---
name: memory-cleanup
description: 自动清理过期/冗余记忆，保持 memory 精简。只删除有明确过期依据的条目，不确定的不动。
version: 1.0.0
---

# memory-cleanup

每周日 00:00 自动运行，扫描 MEMORY.md 并清理过期内容。

## 清理规则

- 含版本号（如 `v1.2.3`）的引用条目 → 删除
- 旧日期（超过1周）+ 包含"一次性"关键词 → 删除
- 精确重复条目 → 保留第一个，其余删除
- USER.md 完全不参与扫描

## 安装

```bash
# 首次安装
python3 skills/memory-cleanup/install.py

# 预览（不实际执行）
python3 skills/memory-cleanup/install.py --dry-run

# 强制更新（版本不一致时）
python3 skills/memory-cleanup/install.py --force

# 查看已安装版本 vs 仓库版本
python3 skills/memory-cleanup/install.py --dry-run
```

## 版本

当前版本：`1.0.0`

版本历史：
- `1.0.0` — 初始版本：版本号/旧日期/精确重复三类规则，JSON 日志，dry-run 支持

## 日志

运行日志位于 `~/.hermes/logs/memory_cleanup.jsonl`（JSON Lines 格式）。

状态枚举：
- `heartbeat` — 无记忆条目时的心跳
- `clean` — 有条目但无需清理
- `cleaned` — 实际清理了条目

## 手动触发

```bash
# 扫描预览
python3 ~/.hermes/scripts/memory_cleanup.py --dry-run

# 执行清理
python3 ~/.hermes/scripts/memory_cleanup.py
```
