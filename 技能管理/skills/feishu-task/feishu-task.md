# feishu-task

飞书任务管理 skill，基于 `lark-cli` 实现。

## 快速开始

```bash
# 查看未完成任务
python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --completed=false

# 创建任务
python3 ~/.hermes/skills/feishu-task/scripts/create_task.py \
  --summary "整理复盘文档" --due "+3d"

# 完成任务（模糊匹配）
python3 ~/.hermes/skills/feishu-task/scripts/complete_task.py --query "CSS播客"

# 统计概览
python3 ~/.hermes/skills/feishu-task/scripts/stats.py

# 搜索任务
python3 ~/.hermes/skills/feishu-task/scripts/search_tasks.py --query "关键词"
```

## 核心特点

- **日期解析**：截止日期直接透传给 lark-cli，支持 `+2d`、`+1w` 等相对格式
- **模糊匹配**：使用 Python difflib，阈值 60%
- **批量操作**：串行执行，带进度反馈（每10个换行）
- **分页**：自动翻页，最多取 1000 条

## 关键坑点

1. `+complete` 只能用 `--task-id` flag，不能用位置参数
2. `tasks list` 成功返回 `{"code": 0}`，`+complete` 成功返回 `{"ok": true}`
3. `tasks delete` 必须加 `--yes`
4. `completed_at` 是毫秒时间戳，需除 1000

## 文件结构

```
~/.hermes/skills/feishu-task/
├── SKILL.md                        # 主文档
├── scripts/
│   ├── list_tasks.py              # 查看任务
│   ├── create_task.py             # 创建任务
│   ├── complete_task.py           # 完成任务
│   ├── batch_complete.py          # 批量完成
│   ├── search_tasks.py            # 搜索任务
│   └── stats.py                   # 统计概览
└── references/
    └── api-field-diff.md          # API 字段差异速查
```

## 状态

✅ 已完成（2026-05-22）
