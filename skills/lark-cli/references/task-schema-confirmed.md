# tasks list 官方 schema 验证（2026-05-22）

## 确认的参数

| 参数 | 类型 | 默认值 | 最大值 | 说明 |
|------|------|--------|--------|------|
| `page_size` | integer | 50 | **100** | 之前以为无上限，实测 schema 确认 max=100 |
| `completed` | boolean | 不过滤 | — | `true`=已完成，`false`=未完成 |
| `page_token` | string | — | — | 分页标记，有更多数据时返回 |
| `type` | string | my_tasks | — | 只支持 `my_tasks` |
| `agent_task_status` | integer | — | 4 | 智能体任务细分状态（1-4） |

## 返回字段（关键）

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | **enum: `todo` / `done`**（只有这两种，不存在其他状态） |
| `completed_at` | string (ms) | 毫秒时间戳，可计算完成时长 |
| `created_at` | string (ms) | 毫秒时间戳 |
| `due.timestamp` | string (ms) | 截止时间毫秒时间戳 |
| `due.is_all_day` | boolean | 是否全天日期 |
| `guid` | string | 任务唯一 ID，完成/删除时用 |
| `summary` | string | 任务标题 |

## 分页

```bash
# 方式一：--page-all 自动翻页（推荐）
lark-cli task tasks list --params '{"completed": false, "page_size": 100}' --format json --page-all

# 方式二：手动循环 has_more
lark-cli task tasks list --params '{"completed": false, "page_size": 100}' --format json
# → 读 has_more 和 page_token，循环直到 has_more=false
```

## tasks delete

- `task_guid` 是 **path 参数**，不是 query 参数
- 必须通过 `--params` 传递

```bash
# ✅ 正确
lark-cli task tasks delete --params '{"task_guid": "<guid>"}' --yes

# ❌ 错误：--task-id 不是 delete 的参数
lark-cli task tasks delete --task-id <guid>
```

## +create --due

`--due` 参数**原生支持相对日期格式**，无需 Python 预解析：

```bash
# 这些都可以直接传，不需要 python dateutil 处理
--due "+2d"       # 2天后
--due "+1w"       # 1周后
--due "2026-05-25" # 标准日期
```

## +search

```bash
# 关键词搜索（支持 --page-all）
lark-cli task +search --query "关键词" --completed false --format json --page-all

# 搜索已完成的
lark-cli task +search --query "关键词" --completed true --format json --page-all
```

## +complete 成功判断

```
成功 → {"code": 0, ...}
失败 → 非 0 code
```

**不是 `{"ok": true}`**，判断成功用 `grep '"code": 0'`。
