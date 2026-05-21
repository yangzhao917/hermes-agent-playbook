# Hermes Agent Playbook

> 杨钊的 Hermes Agent 使用经验与避坑指南

**仓库：** https://github.com/yangzhao917/hermes-agent-playbook
**维护者：** 杨钊 [@yangzhao917](https://github.com/yangzhao917)

---

## Skills

每个 skill 均遵循 Hermes Agent 官方格式：`SKILL.md` + 可选 `scripts/`。

| Skill | 描述 | 触发方式 |
|-------|------|---------|
| `memory-cleanup` | 自动清理 MEMORY.md 过期/冗余条目 | 手动或 cron |
| `morning-reminder` | 每日推送今日+明日飞书日历摘要 | cron |
| `daily-review` | 每日生成复盘文档写入飞书（幂等） | cron |
| `friend-social-review` | 人际关系复盘，以朋友口吻给建议 | 手动对话触发 |

---

## 快速使用

```bash
# 清理记忆（预览）
python3 ~/.hermes/skills/memory-cleanup/scripts/memory_cleanup.py --dry-run

# 晨间日历
python3 ~/.hermes/skills/morning-reminder/scripts/morning_reminder.py

# 生成复盘
python3 ~/.hermes/skills/daily-review/scripts/daily_review.py

# 人际复盘：直接对我说"帮我复盘一下xxx"
```

---

## 目录结构

```
hermes-agent-playbook/
├── skills/
│   ├── memory-cleanup/
│   │   ├── SKILL.md
│   │   └── scripts/memory_cleanup.py
│   ├── morning-reminder/
│   │   ├── SKILL.md
│   │   └── scripts/morning_reminder.py
│   ├── daily-review/
│   │   ├── SKILL.md
│   │   └── scripts/daily_review.py
│   └── friend-social-review/
│       └── SKILL.md
└── README.md
```

---

## 平台文档

- [飞书](./飞书/README.md) — Token 管理、日历/任务规范
- [定时任务](./定时任务/README.md) — cron 架构规范
- [用户规约](./用户规约/README.md) — 用户偏好

## License

MIT
