# Hermes Agent Playbook

> Hermes Agent 使用经验与自动化 playbook 仓库 | 适合 AI Agent 工程师求职者

**仓库：** https://github.com/yangzhao917/hermes-agent-playbook
**维护者：** 杨钊 [@yangzhao917](https://github.com/yangzhao917)

---

## 这是什么

这是一个 **可安装的 playbook 仓库**。

它把 Hermes Agent 的使用经验沉淀成独立的 skill 包，每个包可以单独安装、自动配置定时任务、自动同步更新。

适用场景：
- 想让 Agent 每天自动生成复盘文档 → 安装 `daily-review`
- 想每天早上自动看日历 → 安装 `morning-reminder`
- 想自动清理过期记忆 → 安装 `memory-cleanup`
- 需要人际关系复盘 → 使用 `friend-social-review`

---

## 快速安装

```bash
# 克隆仓库
git clone https://github.com/yangzhao917/hermes-agent-playbook.git
cd hermes-agent-playbook

# 安装任意 skill
python3 skills/memory-cleanup/install.py
python3 skills/morning-reminder/install.py
python3 skills/daily-review/install.py
python3 skills/friend-social-review/install.py

# 预览安装动作（不实际执行）
python3 skills/<skill>/install.py --dry-run

# 更新已安装的 skill（仓库更新后）
python3 skills/<skill>/install.py --force

# 查看当前版本状态
python3 skills/<skill>/install.py --dry-run
```

---

## 目录结构

```
hermes-agent-playbook/
├── skills/                          # 可独立安装的 skill 包
│   ├── lib/                        # 共享 cron wrapper 工具库（所有自动 skill 共用）
│   │   └── cron.py
│   ├── memory-cleanup/              # 每周自动清理过期记忆
│   │   ├── SKILL.md
│   │   ├── VERSION
│   │   ├── scripts/memory_cleanup.py
│   │   └── install.py
│   ├── morning-reminder/            # 每日 07:30 日历推送
│   │   ├── SKILL.md
│   │   ├── VERSION
│   │   ├── scripts/morning_reminder.py
│   │   └── install.py
│   ├── daily-review/               # 每日 23:30 复盘文档
│   │   ├── SKILL.md
│   │   ├── VERSION
│   │   ├── scripts/daily_review.py
│   │   └── install.py
│   └── friend-social-review/        # 人际关系复盘（手动触发）
│       ├── SKILL.md
│       ├── VERSION
│       ├── scripts/check.py
│       └── install.py
└── README.md
```

---

## 各 skill 简介

| Skill | 运行方式 | 触发时间 | 版本 |
|-------|---------|---------|------|
| `memory-cleanup` | 自动 | 每周日 00:00 | 1.0.0 |
| `morning-reminder` | 自动 | 每日 07:30 | 1.0.0 |
| `daily-review` | 自动 | 每日 23:30 | 1.0.0 |
| `friend-social-review` | 手动 | 对话中触发 | 2.0.0 |

---

## 更新机制

每个 skill 独立版本号，install.py 自动检测版本差异：

```
仓库版本: 1.1.0
已安装版本: 1.0.0

版本不一致（已安装 1.0.0，仓库 1.1.0）
使用 --force 强制安装
```

---

## 核心设计原则

1. **幂等性** — 重复安装不重复创建 cron job，已存在则跳过
2. **版本可控** — 每个 skill 有 `VERSION` 文件，更新前会提示版本差异
3. **dry-run 预览** — 所有安装操作支持 `--dry-run`，安装前可确认
4. **per-skill 独立** — 每个 skill 自包含（SKILL.md + scripts/ + install.py），互不依赖

---

## 平台文档（不随 skill 安装）

- [飞书](./飞书/README.md) — Token 管理、日历/任务规范
- [定时任务](./定时任务/README.md) — cron 架构规范
- [用户规约](./用户规约/README.md) — 用户偏好
- [配置指南](./配置指南/README.md) — 环境配置

## License

MIT
