---
name: memory-cleanup
description: 清理过期/冗余记忆，保持 memory 精简。只删除有明确过期依据的条目，不确定的不动。
triggers:
  - 用户说「清理记忆」
  - 每周定时触发
---

# SKILL: memory-cleanup

记忆清理机器人。保持 memory 精简，只删除有明确过期依据的条目。

## 清理规则

**只删除以下情况：**

1. **【重复内容】** 同一字符串出现多次，保留第一条
2. **【已失效的临时教训】** 含旧日期（>1周）的一次性事件记录
3. **【过期状态数据】** 含版本号（v1.2.3、CLI 1.0.15 等）的引用
4. **【矛盾记录】** 基于关键词共现检测矛盾（如同时含"在职"和"离职"）

**不动以下内容：**
- USER.md — 用户身份、偏好、习惯
- skill/playbook 文档 — 规范和流程
- cron 配置（jobs.json）

## 验证

```bash
python3 ~/.hermes/scripts/memory_cleanup.py --dry-run
# 确认删除条目预览无误后再执行
```

## 研究参考

基于 Lilian Weng (LLM-powered Autonomous Agents, 2023) 和 Generative Agents (Park et al., 2023) 的记忆模型设计。

详见 `references/memory-research.md`。

## 日志

**脚本位置**：`~/.hermes/scripts/memory_cleanup.py`

**日志**：`~/.hermes/logs/memory_cleanup.jsonl`

## 支持文件

**脚本**：
- `scripts/memory_cleanup.py` — 记忆条目清理（支持 `--dry-run` 预览）
- `scripts/usage_cleanup.py` — 清理 skills/.usage.json 中的过期记录（支持 `--dry-run` 预览）

运行态 canonical 路径：

```bash
python3 ~/.hermes/skills/productivity/memory-cleanup/scripts/memory_cleanup.py --dry-run
```

兼容 wrapper：

```bash
python3 ~/.hermes/scripts/memory_cleanup.py --dry-run
```

> 注意：`usage_cleanup.py` 由本次会话创建，用于解决「技能目录已删除但 .usage.json 仍有记录」的问题。以后清理 skills 目录时，同步运行此脚本。

日志记录类型：

| status | 含义 | deleted |
|--------|------|---------|
| `heartbeat` | 无记忆文件，跳过 | 无 |
| `clean` | 有记忆但无需清理 | 0 |
| `cleaned` | 实际执行了删除 | >0 |

每条日志含：`timestamp`、`status`、`total`、`deleted_count`、`kept_count`、`duration_ms`

> ⚠️ cron 环境 memory tool 不可用（`skip_memory=True`），必须用 Python 脚本执行。
