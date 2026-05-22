---
name: feishu-task
description: 飞书任务管理 skill，基于 lark-cli 实现任务 CRUD、逾期预警、统计概览。当用户说「查看任务」「查看待办」「我的任务」「飞书任务」「完成任务」「创建任务」时加载。
version: 1.1.0
category: productivity
---

## 触发规则

- 「查看任务」「查看待办」「我的任务」「飞书任务」
- 「创建任务」「添加待办」
- 「完成任务」「删除任务」「搜索任务」
- 「任务统计」「任务概览」

## 速查

| 操作 | 命令 |
|------|------|
| 查未完成任务 | `python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --completed=false` |
| 查已完成任务 | `python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --completed=true` |
| 创建任务 | `python3 ~/.hermes/skills/feishu-task/scripts/create_task.py --summary "标题" --due "+2d"` |
| 完成任务（模糊） | `python3 ~/.hermes/skills/feishu-task/scripts/complete_task.py --query "关键词"` |
| 批量完成 | `python3 ~/.hermes/skills/feishu-task/scripts/batch_complete.py --guids "guid1,guid2"` |
| 搜索任务 | `python3 ~/.hermes/skills/feishu-task/scripts/search_tasks.py --query "关键词"` |
| 统计概览 | `python3 ~/.hermes/skills/feishu-task/scripts/stats.py` |

## 边界条件

**不负责：**
- 日历操作 → 用 `lark-cli calendar`
- 文档操作 → 用 `lark-cli docs`

## 依赖

- Python 3：`python3`（lark-cli 已在 PATH）
- 依赖包：无（lark-cli 自带 HTTP 客户端）

## 脚本目录

```
~/.hermes/skills/feishu-task/scripts/
├── list_tasks.py       # 查看任务列表
├── create_task.py      # 创建任务
├── complete_task.py     # 完成任务（模糊匹配）
├── batch_complete.py   # 批量完成任务
├── search_tasks.py     # 搜索任务
└── stats.py            # 统计概览
```

## 调用方式

> **技能加载原则：**
> - 新技能 / 久未用的技能 → 先 `skill_view` 再执行，避免遗漏更新
> - 熟悉稳定的技能 → 可直接调脚本，但定期核对 skill 文档有无更新
> - 原则：避免"我以为我记得"导致的过时调用

```bash
# 查看未完成任务
python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --completed=false

# 统计概览
python3 ~/.hermes/skills/feishu-task/scripts/stats.py

# 搜索任务
python3 ~/.hermes/skills/feishu-task/scripts/search_tasks.py --query "关键词"

# 创建任务
python3 ~/.hermes/skills/feishu-task/scripts/create_task.py --summary "任务标题" --due "+2d"

# 完成任务（模糊匹配）
python3 ~/.hermes/skills/feishu-task/scripts/complete_task.py --query "CSS播客"

# 批量完成
python3 ~/.hermes/skills/feishu-task/scripts/batch_complete.py --guids "guid1,guid2"
```

## 显示格式规范

**两条铁律：**

1. **截止日期显示具体日期**（如 `🔴 05/22`），禁止相对天数（`1天后到期`、`2天后到期`）
2. **输出必须人类可读**，不能只贴 raw 输出

用户原话：「你要告诉我具体的东西」「告诉我具体内容」——raw 脚本输出不算完成任务，要整理成表格/列表再呈现。

正确流程：脚本执行 → 整理成可读格式 → 给用户看。

正确格式：
- `🔴 05/22` — 今天到期
- `🟡 05/23` — 明天到期
- `📅 06/05` — 未来某天
- `⚠️ 05/20 (逾期 2 天)` — 已逾期

禁止格式：`1 天后到期`、`2 天后到期`、`还有3天`、直接贴脚本 stdout

## 关键实现细节

### 成功判断
- `tasks list`（API命令）：成功返回 `{"code": 0}`
- `+complete`/`+create`（快捷命令）：成功返回 `{"ok": true}`
- 两者不同，解析时必须区分

### 日期解析
- `tasks list` 的 `due.timestamp`：**毫秒级**时间戳，需除 1000
- `+get-my-tasks` 的 `due_at`：ISO 字符串，需 `datetime.fromisoformat()`

### 批量完成
必须**串行**执行，每次单独 `--task-id`，禁止并行（输出交织无法判断成败）。

### 模糊匹配
使用 `rapidfuzz`，阈值 60%。

## 相关技能

- `lark-cli`：底层飞书 CLI 工具
- `lark-task`（官方）：飞书任务完整覆盖，但**缺少模糊匹配、批量操作、统计概览**；这三个场景继续用 feishu-task
- `lark-calendar`（官方）：飞书日历基础覆盖，但**缺少相对日期快捷键、可读输出、删除确认dry-run**；需要这些功能时用 `feishu-calendar`

## 参考资料

- `references/api-field-diff.md` — API 字段差异速查（成功判断、日期解析、坑点）
