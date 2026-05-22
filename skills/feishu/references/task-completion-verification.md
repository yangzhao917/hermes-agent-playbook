# 任务完成验证 · Task Completion Verification

## 核心陷阱（2026-05-19 实测）

### `get-my-tasks` 是混合列表，不能用于验证完成状态

**现象：** `lark-cli task get-my-tasks` 返回的任务列表中，已完成的任务也显示在其中（没有 `[x]` 标记或特殊区分），导致无法判断任务真实状态。

**实测（2026-05-19）：** 批量完成 46 个历史任务后，`get-my-tasks` 仍然显示所有 46 个任务，无法区分已完成和未完成。

### 正确验证方式

```bash
# ✅ 验证任务是否真正完成：查 completed=true 列表
lark-cli task list --completed-status done --page-size 100

# ✅ 验证任务是否未完成：查 completed=false 列表
lark-cli task list --completed-status not_started --page-size 100

# ✅ 单个任务真实状态：查 status 字段
lark-cli task get <task_guid> --format json | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
t=d.get('data',{}).get('task',{})
print('summary:', t.get('summary'))
print('status:', t.get('status'))       # done=已完成, todo=未完成
print('completed_at:', t.get('completed_at'))  # 0=未完成, 有时间戳=已完成
"
```

### 完成 vs 未完成字段对照

| 字段 | 未完成 | 已完成 |
|------|--------|--------|
| `status` | `todo` | `done` |
| `completed_at` | `0` | 毫秒时间戳字符串（如 `1778958277000`） |

### 工作流：批量完成任务后的验证步骤

```bash
# 1. 批量完成任务
for guid in "${GUIDS[@]}"; do
  lark-cli task +complete --task-id "$guid"
done

# 2. 验证：completed=true 列表中是否包含了刚完成的任务
lark-cli task list --completed-status done --page-size 100 --format json \
  | python3 -c "
import json,sys
done=json.load(sys.stdin)
done_guids={t['guid'] for t in done.get('data',{}).get('items',[])}
for g in ${GUIDS[@]}; print(g, '✅ done' if g in done_guids else '⚠️ NOT found')
"

# 3. 验证：not_started 列表中是否还残留
lark-cli task list --completed-status not_started --page-size 100 --format json \
  | python3 -c "
import json,sys
pending=json.load(sys.stdin)
pending_guids={t['guid'] for t in pending.get('data',{}).get('items',[])}
for g in ${GUIDS[@]}: print(g, '⚠️ STILL pending' if g in pending_guids else '✅ removed')
"
```

## `lark-cli task` 子命令速查

| 操作 | 命令 |
|------|------|
| 完成任务 | `lark-cli task +complete --task-id <guid>` |
| 验证已完成 | `lark-cli task list --completed-status done` |
| 验证未完成 | `lark-cli task list --completed-status not_started` |
| 查看单个任务 | `lark-cli task get <guid>` |
| 创建任务 | `lark-cli task +create --summary "标题"` |
| 添加执行人 | `lark-cli task member add <guid> --members <openid> --role assignee` |

> 注意：`+complete` 是 `lark-cli` 特有的 `task` 子命令格式（加号前缀），不是 `complete`。
