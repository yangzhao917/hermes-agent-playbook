# feishu-task Skill 设计方案 (2026-05-22)

## 背景

计划开发一个飞书任务管理 skill，支持自然语言驱动的任务 CRUD 操作。

## 功能范围

1. **查看待办** — 今日/本周/所有/只看逾期
2. **创建任务** — 自然语言解析日期，如"周五前交PPT"
3. **完成任务** — 模糊匹配任务名，如"把量子黑客松那个任务完成"
4. **清理过期任务** — 批量标记完成
5. **逾期预警** — 快到期+已过期任务汇总
6. **统计概览** — 本周新增/完成/逾期数量
7. **任务搜索** — 关键词查找

## 工具清单

| 工具 | 说明 |
|------|------|
| `dateutil.parser` | 日期解析（需安装 `python-dateutil`） |
| `rapidfuzz` | 模糊匹配（需安装，比 difflib 快10-100倍） |
| `datetime` | 标准库，日期计算/时间戳 |
| `json` | 标准库，解析 lark-cli 输出 |
| `re` | 标准库，字符串处理（regex 快速拦截常见日期格式） |

## 关键架构决策

### 1. 日期解析分层策略（快慢分离）

```
用户输入 "周五" / "下周一" / "三天后"
    ↓
regex 匹配常见模式（常见格式覆盖率 80%+）
    ↓ 命中则直接用
    ↓ 未命中
dateutil.parser 兜底（慢但全）
```

### 2. 缓存策略

| 操作 | 策略 |
|------|------|
| 读（查看列表） | session 级缓存，同 session 不重复拉 API |
| 写（创建/完成/更新） | 实时 API + 重新拉取验证 |

### 3. 批量操作

- **串行执行**：禁止并行（输出交织无法判断成败）
- **成功率判断**：`grep '"code": 0'`
- **缓冲**：每两个请求之间 `sleep 0.2`
- **限流处理**：遇到非0返回码等待3秒后重试一次

### 4. 确认机制

批量清理前必须先显示影响范围（"即将完成 30 个过期任务，是否继续？"），用户确认后再执行。

## 飞书任务 API 关键细节（2026-05-22 官方 schema 验证）

### page_size 上限
- **100**（schema `"max": "100"`，不是"无上限"）

### 关键命令

```bash
# 查未完成任务
lark-cli task tasks list --params '{"completed": false, "page_size": 100}' --format json

# 查已完成任务
lark-cli task tasks list --params '{"completed": true, "page_size": 100}' --format json

# 自动翻页（推荐）
lark-cli task tasks list --params '{"completed": false, "page_size": 100}' --format json --page-all

# 完成任务
lark-cli task +complete --task-id <guid>

# 删除任务（task_guid 是 path 参数，必须用 --params）
lark-cli task tasks delete --params '{"task_guid": "<guid>"}' --yes

# 创建任务（必须带 --assignee）
lark-cli task +create --summary "标题" --due "+2d" --assignee <open_id>
# --due 原生支持相对格式（+2d, +1w 等），无需预解析
```

### status 字段
- **enum: `todo` / `done`**（只有这两种，不存在其他状态）

### 截止日期字段解析差异

| 数据源 | 字段 | 格式 | 示例解析 |
|--------|------|------|---------|
| `+get-my-tasks` | `due_at` | ISO 字符串 | `2026-05-25T00:00:00+08:00` |
| `tasks list` | `due.timestamp` | 毫秒时间戳 | `1748131200000` → `05/25` |

### 成功判断（2026-05-22 实测修正）

| 命令 | 成功返回 | 判断方式 |
|------|---------|---------|
| `+complete` / `+reopen` | `{"ok": true, ...}` | `grep '"ok": true'` |
| `+create` | `{"ok": true, ...}` | `grep '"ok": true'` |
| `tasks list` | `{"ok": true, ...}` | `grep '"ok": true'` |
| `tasks delete` | `{"code": 0, ...}` | `grep '"code": 0'` |
| `tasks patch` | `{"code": 0, ...}` | `grep '"code": 0'` |

> ⚠️ **注意：** `+complete` 是 `ok:true`，不是 `code:0`。两个不同的 HTTP 响应格式，不要混淆。

### 批量完成（禁止并行）

```bash
# ✅ 正确：串行
for guid in $GUIDS; do
  r=$(lark-cli task +complete --task-id "$guid" 2>&1)
  echo "$r" | grep -q '"ok": true' && echo "OK" || echo "FAIL"
  sleep 0.2
done

# ❌ 错误：并行 xargs -P
```

### rate limit

- page_size 上限：**100**（schema 确认 `"max": "100"`）
- 飞书 API 无明确 QPS 上限数值
- 保守做法：批量操作每两个请求间加 `sleep 0.2`
- 限流时自动等待3秒重试

### 可用字段

- `completed_at`（毫秒时间戳）→ 可计算完成时长
- `created_at`（毫秒时间戳）→ 可计算新建时间
- `due.is_all_day`（boolean）→ 判断是否全天日期

### 获取当前用户 open_id

```bash
lark-cli contact +search-user --user-ids 'me' --format json
# 返回: open_id = ou_5b875f5ec5752b06832bb240ad482ec0
```

### `+search` 命令要点

```bash
# --completed 是 flag（不是 --complete），不接受值
lark-cli task +search --completed --query "关键词"   # 已完成
lark-cli task +search --query "关键词"              # 不过滤（全部）
# --due 格式: start,end（ISO 日期）
lark-cli task +search --due '2026-05-01,2026-06-30' --page-all --page-limit 40
```

### `tasks patch` 注意事项

- `update_fields` **必填**，PATCH 请求必须带上要修改的字段名数组
- status 不在白名单中，标记完成只能用 `+complete --task-id`
- task_guid 是 path 参数，必须用 `--params '{"task_guid": "..."}'`

### 删除任务

```bash
# task_guid 是 path 参数，必须用 --params
lark-cli task tasks delete --params '{"task_guid": "<guid>"}' --yes
# --yes 必须加（high-risk-write）
```

## 状态

🟡 设计阶段，待开发
