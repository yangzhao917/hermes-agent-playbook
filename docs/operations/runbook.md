# 运维手册

## 腾讯云运行态

AgentOS 当前运行在腾讯云轻量 Ubuntu 服务器，运行用户是 `ubuntu`。

关键路径：

```text
~/.hermes/agent-os
~/.hermes/skills
~/.hermes/scripts
~/.hermes/state/agentos
~/.hermes/logs/agentos
~/.hermes/cron/jobs.json
```

## 验证命令

```bash
python3 -m py_compile \
  ~/.hermes/skills/mainline-governance/scripts/mainlines.py \
  ~/.hermes/scripts/morning_reminder.py \
  ~/.hermes/skills/daily-review/scripts/daily_review.py \
  ~/.hermes/skills/weekly-review/scripts/weekly_review.py

python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py list
python3 ~/.hermes/scripts/daily_review.py --check-path
python3 ~/.hermes/scripts/weekly_review.py --check-path
```

## 飞书 CLI Workspace

Hermes 下的 lark-cli 调用必须带：

```bash
HERMES_HOME=/home/ubuntu/.hermes
```

每日和每周复盘脚本已在内部设置这个环境变量。

## 变更策略

- 不提交 secrets、运行态 state、日志或个人 token。
- 除非改 gateway 配置，否则不重启 Hermes gateway。
- 只有在杨钊确认 diff 后才 commit / push。
