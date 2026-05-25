---
name: feishu-task
description: 飞书任务管理（查看/创建/完成/删除/搜索/批量处理）
version: 1.1.0
category: productivity
tags: [feishu, task, todo, checklist]
---

# feishu-task ✅

> ⚠️ **禁区**
> - `+complete` 成功返回 `{"ok": true}`，**不是** `{"code": 0}`
> - `due.timestamp` 是**毫秒级**（不是秒级）
> - `+create` 必须带 `--assignee`（用户 open_id）
> - `tasks delete` 参数是 `--params '{"task_guid":"..."}'`，不是 `--task-id`
> - `tasks patch` 的 `status` **不在白名单**，标记完成只能用 `+complete`
> - **脚本路径是 `productivity/feishu-task/scripts/`**，不是 `feishu-task/scripts/`

## 触发条件

用户说「查看任务」「我的待办」「创建任务」「完成任务」「删除任务」「搜索任务」「逾期预警」「批量完成」「批量删除」「本周完成了什么」

## 速查

| 操作 | 命令 |
|------|------|
| 查未完成任务 | `python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --status todo` |
| 查已完成任务 | `python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --status done` |
| 查所有任务 | `python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --status all` |
| 创建任务 | `python3 ~/.hermes/skills/feishu-task/scripts/create_task.py --summary "标题" --due "+3d"` |
| 完成任务 | `python3 ~/.hermes/skills/feishu-task/scripts/complete_task.py --task-id <guid>` |
| 删除任务 | `python3 ~/.hermes/skills/feishu-task/scripts/delete_task.py --task-guid <guid> [--yes]` |
| 搜索任务 | `python3 ~/.hermes/skills/feishu-task/scripts/search_tasks.py --query "关键词"` |
| 修改截止时间 | `lark-cli task +update --task-id <guid> --due "YYYY-MM-DD HH:MM:SS"` |
| 批量完成任务 | `python3 ~/.hermes/skills/feishu-task/scripts/batch_complete.py --overdue [--days 3] [--yes]` |
| 批量删除任务 | `python3 ~/.hermes/skills/feishu-task/scripts/batch_delete.py --task-guid <g1> --task-guid <g2> [--yes]` |

## 完整示例

```bash
# 查看所有待办
python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --status todo

# 创建任务（相对日期）
python3 ~/.hermes/skills/feishu-task/scripts/create_task.py \
  --summary "提交项目方案" \
  --due "+3d"

# 创建任务（绝对日期）
python3 ~/.hermes/skills/feishu-task/scripts/create_task.py \
  --summary "提交项目方案" \
  --due "2026-05-28"

# 完成任务
python3 ~/.hermes/skills/feishu-task/scripts/complete_task.py \
  --task-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# 删除任务
python3 ~/.hermes/skills/feishu-task/scripts/delete_task.py \
  --task-guid "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" --yes

# 搜索任务
python3 ~/.hermes/skills/feishu-task/scripts/search_tasks.py --query "项目"

# 批量完成已逾期任务（先预览，确认后执行）
python3 ~/.hermes/skills/feishu-task/scripts/batch_complete.py --overdue
# 超过 3 天未完成也算逾期
python3 ~/.hermes/skills/feishu-task/scripts/batch_complete.py --overdue --days 3
# 指定 guid 批量完成
python3 ~/.hermes/skills/feishu-task/scripts/batch_complete.py --task-id <g1> --task-id <g2>

# 批量删除任务
python3 ~/.hermes/skills/feishu-task/scripts/batch_delete.py --task-guid <g1> --task-guid <g2>
```

## 用户 open_id

```
ou_5b875f5ec5752b06832bb240ad482ec0
```

## 时间格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 相对天数 | `+2d` | 2 天后 |
| 相对周数 | `+1w` | 1 周后 |
| 绝对日期 | `2026-05-25` | 截止当天 |

> `--due` 原生支持相对格式，lark-cli 内部解析，无需预计算
>
> **修改截止时间**：`lark-cli task +update --task-id <guid> --due "2026-05-25 20:00:00"`（支持带时间的精确截止）

## API 分页

`tasks list` API 的 `page_size` 上限是 **100**，脚本内部自动处理 `--page-all` 翻页

## 命令响应速查

| 命令 | 成功返回 | 判断方法 |
|------|---------|---------|
| `+create` | `{"ok": true}` | `data.get("ok") is True` |
| `+complete` | `{"ok": true}` | `data.get("ok") is True` |
| `+reopen` | `{"ok": true}` | `data.get("ok") is True` |
| `tasks list` | `{"code": 0}` | `data.get("code") == 0` |
| `tasks delete` | `{"code": 0}` | `data.get("code") == 0` |
