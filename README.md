# Hermes Agent Playbook

> Hermes Agent 使用经验与避坑指南 | 基于 v0.14.0

**仓库：** https://github.com/yangzhao917/hermes-agent-playbook

**维护者：** 杨钊（[@yangzhao917](https://github.com/yangzhao917)）

---

## 快速上手

**首次阅读顺序（建议）：**

1. [用户规约](./用户规约/README.md) — 必读，了解助手的行为规则
2. [飞书](./飞书/README.md) — 了解飞书文档/日历/任务的存放规范和 Token 管理
3. [定时任务](./定时任务/README.md) — 了解每日复盘生成和晨间提醒的机制
4. [skills](./skills/) — 根据需要查阅具体 skill 文档

**常见操作对应的文档：**

| 操作 | 文档 |
|------|------|
| 创建飞书任务 | [feishu-task](../飞书/feishu-task/SKILL.md) |
| 查看飞书日历 | [feishu-calendar](../飞书/feishu-calendar/SKILL.md) |
| 写每日复盘 | [daily-review](./skills/daily-review.md) |
| 清理过期记忆 | [memory-cleanup](./skills/memory-cleanup.md) |
| 飞书 Token 续期 | [飞书 README - Token 管理](./飞书/README.md#token-管理) |
| 查看 cron 任务 | [定时任务](./定时任务/README.md) |

---

## 内容结构（按场景）

```
hermes-agent-playbook/
├── README.md
├── 飞书/                  # 平台文档 + 所有飞书 skill
│   ├── README.md          # Token、folder结构、联动规则
│   ├── feishu-task/
│   ├── feishu-calendar/
│   └── feishu-cli/
├── 微信/                  # 微信平台文档
├── skills/                # 独立 skill（每个含脚本 + 安装脚本）
│   ├── memory-cleanup/
│   │   ├── SKILL.md
│   │   ├── scripts/memory_cleanup.py
│   │   └── install.py
│   ├── morning-reminder/
│   │   ├── SKILL.md
│   │   ├── scripts/morning_reminder.py
│   │   └── install.py
│   ├── daily-review/
│   │   ├── SKILL.md
│   │   ├── scripts/daily_review.py
│   │   └── install.py
│   └── friend-social-review/
├── 定时任务/              # cron 规范（跨平台通用）
├── 用户规约/              # 用户偏好（跨平台通用）
└── 配置指南/              # 环境配置（跨平台通用）
```

---

## 核心文档

| 目录 | 内容 |
|------|------|
| [飞书](./飞书/README.md) | 飞书平台规范（Token管理、日历/任务联动） |
| [微信](./微信/README.md) | 微信消息队列、意图识别、分发规则 |
| [定时任务](./定时任务/README.md) | cron 架构规范、复盘总结模板 |
| [用户规约](./用户规约/README.md) | 用户偏好、飞书操作规范、时间计算规范 |
| [配置指南](./配置指南/README.md) | 安装配置、更新、新功能说明 |
| [skills](./skills/) | 通用 skill（morning-reminder、daily-review、friend-social-review、memory-cleanup） |

---

## 内容来源

- 飞书文档（持续同步）
- Hermes Agent v0.14.0 官方更新

## License

MIT
