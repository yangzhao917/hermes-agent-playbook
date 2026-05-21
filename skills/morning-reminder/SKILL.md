---
name: daily-review
description: 每日 23:30 自动生成复盘文档并写入飞书。
version: 1.0.0
---

# daily-review

每日 23:30 (CST) 自动生成复盘总结，写入飞书 `hermesAgent/每日复盘/` 文件夹。

## 安装

```bash
# 首次安装
python3 skills/daily-review/install.py

# 预览
python3 skills/daily-review/install.py --dry-run

# 强制更新
python3 skills/daily-review/install.py --force
```

## 文档模板

生成的文档包含：
- 计划事项（必须填写）
- 完成情况（必须填写）
- 明日待办（必须填写）
- 待跟进（紧迫度标注）
- 后续安排
- 今日日历事件（自动从飞书拉取）

## 版本

当前版本：`1.0.0`

版本历史：
- `1.0.0` — 初始版本，幂等写入（文档存在则覆盖），日历事件参考，自动创建文件夹
