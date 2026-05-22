# 飞书任务命令参考

## 快速查询（推荐）

直接运行 `stats.py`，输出格式化的任务统计：

```bash
python3 ~/.hermes/skills/feishu-task/scripts/stats.py
```

输出：
```
📊 任务统计
  🔴 已过期(N):
    ⚠️ 06/19 CSS播客重录
  🔴 今日到期(N):
    ☐ 任务名称
  🟡 近期待办(N):
    ☐ 06/05 任务名称
```

## lark-cli 原生命令

```bash
# 未完成任务（含已过期）
lark-cli task tasks list --params '{"page_size":50,"completed":false}' --format json

# 已完成任务
lark-cli task tasks list --params '{"page_size":50,"completed":true}' --format json
```

## 任务状态字段

- `status=done` + `completed_at` 有值 = 已完成
- `status=todo` + `completed_at=0` = 未完成

**注意**：`+get-my-tasks` 返回混合列表（已完成+未完成），无法直接区分完成状态。必须用 `tasks list` + `completed` 参数过滤。

## 相关脚本

| 脚本 | 用途 |
|------|------|
| `stats.py` | 统计概览：已过期/今日到期/近期待办 |
| `list_tasks.py` | 完整任务列表 |
| `create_task.py` | 创建任务 |
| `complete_task.py` | 完成任务（模糊匹配） |
| `batch_complete.py` | 批量完成 |
| `search_tasks.py` | 搜索任务 |
