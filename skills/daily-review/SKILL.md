---
name: morning-reminder
description: 每日 07:30 推送今日+明日日历日程摘要到飞书。
version: 1.0.0
---

# morning-reminder

每日 07:30 (CST) 自动查询飞书日历，推送今日和明日日程摘要。

## 安装

```bash
# 首次安装
python3 skills/morning-reminder/install.py

# 预览
python3 skills/morning-reminder/install.py --dry-run

# 强制更新
python3 skills/morning-reminder/install.py --force
```

## 版本

当前版本：`1.0.0`

版本历史：
- `1.0.0` — 初始版本，基于 lark-cli calendar +agenda，每日两次推送
