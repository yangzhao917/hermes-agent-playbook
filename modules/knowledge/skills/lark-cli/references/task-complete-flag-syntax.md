# task +complete / +get-my-tasks flag 语法 (2026-05-20)

## `+get-my-tasks` 的 `--complete` flag 行为

```
--complete         → 查已完成任务
（不传此 flag）    → 查已完成+未完成混合
--complete false   → ❌ 报错 Usage，flag 解析失败
```

**实测：**
```bash
$ lark-cli task +get-my-tasks --complete false --due-end '2025-12-31'
# exit 1，输出帮助文本（flag 不被接受）

$ lark-cli task +get-my-tasks --complete --due-end '2025-12-31'
# exit 0，返回 28 个已完成任务（2025年10月-12月）
```

**结论：**
- `--complete` 单独使用（无值）= 查已完成
- 不传 `--complete` = 查全部（已完成+未完成混杂）
- **`--complete false` / `--complete true` 均不生效**，flag 解析器只认 `--complete` 本身

**正确查未完成任务：用 `tasks list`**：
```bash
lark-cli task tasks list \
  --params '{"completed_status": "not_started", "page_size": 50}' \
  --format json
```

## `+complete` 的 `--task-id` flag

```
--task-id <guid>   → ✅ 正确
<guid>（位置参数）  → ❌ "positional arguments not supported"
```

## 总结

| 需求 | 正确命令 |
|------|---------|
| 查未完成任务 | `tasks list --params '{"completed_status": "not_started"}'` |
| 查已完成任务 | `+get-my-tasks --complete` |
| 查全部（含完成） | `+get-my-tasks` |
| 标记单个完成 | `+complete --task-id <guid>` |
| 批量标记完成 | 串行循环，每次 `+complete --task-id <guid>` |
