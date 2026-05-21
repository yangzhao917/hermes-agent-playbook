# Hermes Agent Playbook

> Hermes Agent 使用经验与避坑指南 | 基于 v0.14.0

**仓库：** https://github.com/yangzhao917/hermes-agent-playbook

**维护者：** 杨钊（[@yangzhao917](https://github.com/yangzhao917)）

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
├── skills/                # 通用 skill（不依赖特定平台）
│   ├── friend-social-review/
│   ├── morning-reminder/
│   └── daily-review/
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
| [skills](./skills/) | 通用 skill（morning-reminder、daily-review、friend-social-review） |

---

## 内容来源

- 飞书文档（持续同步）
- Hermes Agent v0.14.0 官方更新

## License

MIT
