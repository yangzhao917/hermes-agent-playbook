---
name: memory-cleanup
description: 自动清理过期/冗余记忆，保持 MEMORY.md 精简。只删除有明确过期依据的条目，不确定的不动。
trigger: "清理记忆 / 每周记忆清理"
version: 1.0.0
---

# 记忆清理

## 存放位置

- 脚本：`scripts/memory_cleanup.py`（本目录下）
- 日志：`~/.hermes/logs/memory_cleanup.jsonl`（JSON Lines）
- 记忆文件：`~/.hermes/memories/MEMORY.md`

## 安装

```bash
python3 skills/memory-cleanup/install.py
```

## 使用方式

```bash
python3 ~/.hermes/scripts/memory_cleanup.py        # 执行清理
python3 ~/.hermes/scripts/memory_cleanup.py -n     # 预览（不删除）
```

## 清理规则

| 规则 | 条件 | 示例 |
|------|------|------|
| 版本号引用 | 含有 v1.2.3、CLI 1.0.15 等 | `MiniMax CLI v1.0.15` |
| 过期一次性事件 | 含旧日期（>1周）+ 含"一次性" | `2025-05-01 临时方案` |
| 精确重复 | 同一字符串出现多次 | 保留第一条 |
| 矛盾记录 | 同时含"在职"和"离职"等 | 标记待删 |

**不动：** USER.md、skill/playbook 文档、cron 配置

## 日志格式

```json
{"timestamp": "2026-05-21T22:37:29+00:00", "status": "heartbeat", "reason": "no_memory"}
{"timestamp": "2026-05-21T22:37:29+00:00", "status": "clean", "total": 3, "deleted_count": 0}
{"timestamp": "2026-05-21T22:37:29+00:00", "status": "cleaned", "total": 5, "deleted": [...], "deleted_count": 2}
```

| status | 含义 |
|--------|------|
| `heartbeat` | 无记忆文件，跳过 |
| `clean` | 有记忆，无需清理 |
| `cleaned` | 执行了删除 |

## 定时任务

每周日 00:00 UTC 自动执行（job_id: `4af2be6bb68f`），结果推送至当前对话。
