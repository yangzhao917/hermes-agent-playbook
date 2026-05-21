# 飞书集成

> 飞书文档、待办、日历、Token 的操作规范

## 目录

- [文档操作](#文档操作)
- [待办任务](#待办任务)
- [日历操作](#日历操作)
- [Token 管理](#token-管理)

---

## 文档操作

### 创建新文档

1. 先 `lark-cli auth login --domain drive --domain all --recommend` 让用户扫码授权

2. 用 `lark-cli docs +create` 创建文档（transfer_ownership=true）再写入内容

3. 创建后用 `lark-cli file move` 移动到目标目录：

```bash
lark-cli file move DOC_ID --target <FOLDER_TOKEN> --type docx
```

### 文档统一存放目录

- **HermesAgent**（folder_token: `<FOLDER_TOKEN>`）
- 所有 AI 创建的文档统一放这里
- 子目录结构按需创建（每日复盘/项目/知识沉淀等）

### 更新已有文档

```bash
# 完全覆盖全文
lark-cli docs +update --mode overwrite --markdown-file file.md

# 局部替换指定标题下的内容
lark-cli docs +update --mode replace_range --selection-by-title "标题名"
```

> ⚠️ 不要用 `import` 命令追加内容，要覆盖写入用 `+update --mode overwrite`

### 查看已有文档

```bash
lark-cli doc export DOC_ID -o output.md
```

### docx Block API（可靠）

`POST /docx/v1/documents/{doc_id}/blocks/{block_id}/children` 可用，用于插入内容块。飞书文档本身操作推荐用 CLI，Block API 适合程序化写入场景。

---

## 待办任务

> ✅ 现在统一用 `feishu-task` skill（`python3 ~/.hermes/skills/feishu-task/scripts/xxx.py`），不再用直接 curl 调用。

### 查看任务
```bash
python3 ~/.hermes/skills/feishu-task/scripts/list_tasks.py --completed=false
```

### 创建任务
```bash
python3 ~/.hermes/skills/feishu-task/scripts/create_task.py \
  --summary "任务标题" --due "+2d"
```

### 完成任务（模糊匹配）
```bash
python3 ~/.hermes/skills/feishu-task/scripts/complete_task.py --query "关键词"
```

### 统计概览
```bash
python3 ~/.hermes/skills/feishu-task/scripts/stats.py
```

> ⚠️ 任务创建必须带 `--assignee`，否则用户在飞书看不到任务

### 日程与待办联动规则

**新增 / 更新 / 完成 / 删除 时，日程和待办必须同步处理。**

- 新增：同时创建日程 + 待办，执行人/参与人一致
- 更新：同时更新时间
- 完成：同时标记完成（或只留一种）
- 删除：同时删除

---

## 日历操作

### 用户日历 ID

`feishu.cn_<YOUR_CALENDAR_ID>@group.calendar.feishu.cn`

### 创建日程（带参与人）

```bash
curl -X POST "https://open.feishu.cn/open-apis/calendar/v4/calendars/$CAL_ID/events" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "summary": "标题",
    "description": "描述",
    "start_time": {"timestamp": "1779111000", "timezone": "Asia/Shanghai"},
    "end_time": {"timestamp": "1779114600", "timezone": "Asia/Shanghai"},
    "attendees": [{"type": "user", "user_id": "<USER_ID>"}]
  }'
```

### 查询日程

```bash
curl "https://open.feishu.cn/open-apis/calendar/v4/calendars/$CAL_ID/events?start_time=TS&end_time=TS&page_size=50" \
  -H "Authorization: Bearer $TOKEN"
```

### event_id 必须用完整值

从 JSON 响应直接提取，不用终端显示的截断版

---

## Token 管理

### Token 文件

`~/.lark-cli/hermes`（lark-cli 的 token 存放路径）

### 有效期

- access_token：2 小时
- refresh_token：7 天

### 静默刷新

```bash
lark-cli auth refresh
```

### 常见错误码

| 错误码 | 含义 | 处理 |
|--------|------|------|
| 99991677 | access_token 过期 | 刷新 token |
| 20025 | App ID/Secret 缺失 | 检查 .env 文件 |
| 20026 | refresh_token 过期 | 需重新 Device Flow 授权 |
| 193003 | 事件已删除 | 忽略（幂等） |
| 191002 | calendar 无 writer 角色 | 换用户 token |
| 99992402 | field validation failed | 查 API 文档补字段 |

### 授权限制

**7天内不要主动要求用户重新扫码授权**，除非 token 明确失效报错。

---

## 去重原则

日程、待办、文档同一主题保留最新一条，旧的一律删除或归档。

- **日程**：同标题同时段 → 保留一条
- **待办**：同主题 → 保留最新，删旧
- **文档**：同标题或实质同内容 → 保留最新
