---
name: feishu-task
description: 飞书任务管理 skill，支持自然语言驱动的任务 CRUD、逾期预警、统计概览。基于 lark-cli(v1.0.33+) 实现。
version: 1.0.0
---

## 依赖

- Python 3（虚拟环境）：`~/.hermes/hermes-agent/venv/bin/python3`
- `python-dateutil`（日期解析）：`pip install python-dateutil`
- 模糊匹配用标准库 `difflib`（无需安装），threshold=60

## 功能清单

1. **查看待办** — 今日/本周/所有/只看逾期
2. **创建任务** — 自然语言日期，如"周五前交PPT"
3. **完成任务** — 模糊匹配任务名
4. **清理过期任务** — 批量标记完成
5. **逾期预警** — 快到期+已过期任务汇总
6. **统计概览** — 本周新增/完成/逾期数量
7. **任务搜索** — 关键词查找

## 架构决策

### 日期解析

- `+create --due` 原生支持相对日期格式（`+2d`、`+1w`），直接透传给 lark-cli，**不需要 Python 解析**
- `tasks list` 截止日期：`due.timestamp`（毫秒时间戳）→ `datetime.fromtimestamp(int(ts)/1000, tz=sh_tz)`
- 自然周定义：本周一 00:00:00 ~ 本周日 23:59:59（ISO week）

### 模糊匹配

- 使用 Python 标准库 `difflib`（无需安装）
- 匹配阈值：60（低于60说"没找到"）
- 标题短，不需要 jieba 分词

### 成功判断（按命令分开）

| 命令 | 成功判断 |
|------|---------|
| `+complete` / `+reopen` / `+create` / `tasks list` / `+search` | `ok: true` |
| `tasks delete` / `tasks patch` | `code: 0` |

### 批量操作

- **串行执行**：禁止并行（输出交织无法判断成败）
- 批量完成：每两个请求之间 `sleep 0.2`
- 限流处理：非0返回码等待3秒重试一次
- 进度反馈：每完成一个打印 `.`，每10个换行

### 分页

- `tasks list --page-size 100 --page-all`
- `+search --page-all --page-limit 40`

### Assignee

- 创建任务时默认用当前用户 open_id
- 获取方式：`lark-cli contact +search-user --user-ids 'me'`

## 命令速查

```bash
# 查未完成任务（分页取全部）
lark-cli task tasks list --params '{"completed": false, "page_size": 100}' --format json --page-all

# 查已完成任务
lark-cli task tasks list --params '{"completed": true, "page_size": 100}' --format json --page-all

# 搜索任务
lark-cli task +search --query "关键词" --page-all --page-limit 40 --format json

# 完成任务
lark-cli task +complete --task-id <guid>

# 重开任务
lark-cli task +reopen --task-id <guid>

# 创建任务（+due 支持相对格式）
lark-cli task +create --summary "标题" --due "+2d" --assignee <open_id>

# 更新任务（update_fields 必填）
lark-cli task tasks patch --params "{\"task_guid\": \"<guid>\"}" --data "{\"task\": {\"summary\": \"新标题\"}, \"update_fields\": [\"summary\"]}"

# 删除任务
lark-cli task tasks delete --params '{"task_guid": "<guid>"}' --yes

# 获取当前用户 open_id
lark-cli contact +search-user --user-ids 'me' --format json
```

## API 字段差异

| 字段 | `+get-my-tasks` | `tasks list` |
|------|---------------|-------------|
| 截止日期 | `due_at` ISO字符串 | `due.timestamp` 毫秒 |
| 状态 | `status: null` | `status: "todo"/"done"` |
| 创建时间 | ISO字符串 | 毫秒时间戳 |
| 完成时间 | ISO/null | 毫秒时间戳 |

统一使用 `tasks list`（支持状态过滤），不使用 `+get-my-tasks`。

## 逾期推送格式

```
⏰ 逾期预警（截止 {日期}）
1. [任务名] | 逾期 N 天
2. [任务名] | 逾期 N 天
```

## 统计概览格式

```
📊 本周概览
新增: N  完成: N  逾期: N  完成率: XX%

🔥 最久未完成 Top3
1. [任务名] | 截止 MM/DD | 已逾期 N 天
2. ...
```

## 使用示例

### 查看待办
```bash
python3 list_tasks.py --completed=false
# 输出：按逾期/即将到期/无期限分组，显示前20条摘要

python3 list_tasks.py --completed=false --show-all
# 输出：所有未完成任务详细列表
```

> 脚本路径为本地开发路径（`/home/ubuntu/skills/feishu-task/scripts/`），playbook 仓库仅含 SKILL.md

### 创建任务
```bash
python3 create_task.py --summary "整理飞书复盘文档" --due "+3d"
# 截止日期支持：+2d（2天后）、+1w（1周后）、2026-05-25（固定日期）

python3 create_task.py --summary "整理飞书复盘文档" --due "2026-05-25" --dry-run
# dry-run 模式：预览实际 API 请求，不创建
```

### 完成任务（模糊匹配）
```bash
python3 complete_task.py --query "CSS播客"
# 找到匹配任务，匹配度66%以上才有效，否则提示"没找到"

python3 complete_task.py --guid "e8debd23-fcf6-4c60-8f96-cf690b8203bf"
# 直接指定 guid，跳过模糊匹配

python3 complete_task.py --query "CSS" --dry-run
# 预览模式，不实际完成
```

### 批量清理
```bash
python3 batch_complete.py --overdue-only
# 清理所有已逾期任务，逐个确认

python3 batch_complete.py --all
# 清理所有未完成任务（慎用）

python3 batch_complete.py --overdue-only --no-confirm
# 不需要确认直接执行
```

### 统计概览
```bash
python3 stats.py
# 输出：本周新增/完成/逾期数、完成率、Top3 最久未完成任务
```

### 任务搜索
```bash
python3 search_tasks.py --query "CSS播客"
# 支持关键词搜索，返回所有相关任务（含已完成）
```

## 关键坑点

1. **`+complete` / `+reopen` 只能用 `--task-id` flag**，不能用位置参数
2. **`tasks patch` 必须带 `update_fields`**，否则 400
3. **`tasks delete` 必须加 `--yes`**，否则拒绝执行
4. **`+create --due` 传 `YYYY-MM-DD` 时自动设为全天（`is_all_day: true`）**
5. **`completed_at` 是毫秒时间戳**，除1000才能给 `datetime.fromtimestamp`
6. **`page_size` 最大100**，翻页用 `--page-all` 更简单
7. **`tasks list` 成功返回 `{"code": 0}`**，不是 `{"ok": true}`
8. **`+complete/+create/+search` 成功返回 `{"ok": true}`**，不是 `{"code": 0}`
