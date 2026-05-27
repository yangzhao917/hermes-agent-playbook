# Hermes Agent Playbook

> 杨钊的 Hermes Agent 使用经验与避坑指南

**仓库：** https://github.com/yangzhao917/hermes-agent-playbook
**维护者：** 杨钊 [@yangzhao917](https://github.com/yangzhao917)

---

## 自建 Skills

| Skill | 描述 | 触发方式 |
|-------|------|---------|
| `memory-cleanup` | 自动清理 MEMORY.md 过期/冗余条目 | 手动或 cron |
| `morning-reminder` | 每日推送今日+明日飞书日历摘要 | cron |
| `daily-review` | 每日生成复盘文档写入飞书（幂等） | cron |
| `friend-social-review` | 人际关系复盘，以朋友口吻给建议 | 手动对话触发 |

## 第三方 Skills

| Skill | 来源 | 描述 |
|-------|------|------|
| `lark-cli` | [nousresearch/hermes-agent](https://github.com/nousresearch/hermes-agent/tree/main/skills/lark-cli) | 飞书官方 CLI（日历/文档/云空间/任务） |
| `just-one-api` | [justonevec/just-one-api](https://github.com/justonevec/just-one-api) | 小红书/抖音/微博数据搜索 |
| `weread` | [weread](https://github.com/hermes-agent/weread) | 微信读书助手 |
| `mmx-cli` | [mmx-cli](https://github.com/nousresearch/hermes-agent/tree/main/skills/mmx-cli) | MiniMax 文字/图片/视频/语音生成 |
| `web-search-ex-skill` | [nousresearch/hermes-agent](https://github.com/nousresearch/hermes-agent/tree/main/skills/web-search) | 多引擎网络搜索 |
| `humanize-zh` | [hermes-agent/humanize-zh](https://github.com/hermes-agent/humanize-zh) | 中文文本去AI味 |

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
│   ├── friend-social-review/
│   │   └── SKILL.md
│   ├── lark-cli/
│   ├── feishu-task/
│   ├── productivity/feishu/
│   ├── just-one-api/
│   ├── weread/
│   ├── mmx-cli/
│   ├── web-search-ex-skill/
│   └── humanize-zh/
├── 飞书/
│   └── README.md
├── 定时任务/
│   └── README.md
└── 用户规约/
    └── README.md
```

---

## 平台文档

- [飞书](./飞书/README.md) — Token 管理、日历/任务规范
- [定时任务](./定时任务/README.md) — cron 架构规范
- [用户规约](./用户规约/README.md) — 用户偏好

## License

MIT
