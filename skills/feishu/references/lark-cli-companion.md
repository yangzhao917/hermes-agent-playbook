# lark-cli 速查手册

官方飞书 CLI（github.com/larksuite/cli）。

## 核心原则

1. **默认 user 身份** — 无需加 `--user-access-token`，直接操作用户数据
2. **禁止创建 .md FILE 类型** — 统一用飞书原生文档（DOCX）
3. **更新用 `+update --mode overwrite`** — 全量覆盖，不累积版本
4. **`+` 前缀 = 动作命令**（如 `+create`、`+search`、`+agenda`、`+delete`），名词子命令不带 `+`（如 `tasks list`、`tasks patch`）

## 配置路径

```
~/.lark-cli/          # 主配置目录
~/.lark-cli/hermes/   # Hermes 绑定配置
```

## 文档操作

### 创建文档（DOCX，在指定文件夹）

```bash
lark-cli docs +create --title "文档标题" --folder-token FOLDER_TOKEN
```

### 写入/更新内容

```bash
# 全量覆盖（推荐）
lark-cli docs +update --doc DOC_ID --markdown "# 标题\n\n内容" --mode overwrite

# 追加
lark-cli docs +update --doc DOC_ID --markdown "新内容" --mode append
```

### 读取文档

```bash
lark-cli docs +fetch --doc DOC_ID
```

### 搜索文档

```bash
lark-cli docs +search --query "关键词"
```

### 移动文档到文件夹

```bash
lark-cli drive +move --file-token DOC_ID --target-folder-token TARGET_FOLDER
```

### 删除文档

```bash
lark-cli drive +delete --file-token DOC_ID --type docx --yes
```

## 日历操作

### 查询日程（默认当天）

```bash
lark-cli calendar +agenda
```

### 创建日程

```bash
lark-cli calendar +create \
  --summary "日程标题" \
  --start "2026-05-19T10:00:00+08:00" \
  --end "2026-05-19T11:00:00+08:00" \
  --calendar-id feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn
```

### 更新日程

```bash
lark-cli calendar +update --event-id EVENT_ID --summary "新标题"
```

### 删除日程

```bash
lark-cli calendar +delete \
  --event-id EVENT_ID \
  --calendar-id <CALENDAR_ID>
```

⚠️ 必须用 `--params '{"calendar_id":"...","event_id":"..."}'` 或 `--calendar-id` 指定日历 ID。

## 任务操作

### 创建任务

```bash
lark-cli task +create --summary "任务标题" --due "2026-05-20T23:59:00+08:00"
```

### 查看任务列表（正确方式）

```bash
# 未完成任务（布尔过滤）
lark-cli task tasks list --params '{"completed": false, "page_size": 100}' --format json --page-all

# 已完成任务
lark-cli task tasks list --params '{"completed": true, "page_size": 100}' --format json --page-all
```

⚠️ `+get-my-tasks` 返回混合列表（已完成+未完成混杂），无法按状态过滤，**不要用**。

### 完成任务

```bash
lark-cli task +complete --task-id TASK_ID
```

### 更新任务

```bash
# ⚠️ 必须指定 update_fields，否则 400
lark-cli task tasks patch \
  --params '{"task_guid": "TASK_GUID"}' \
  --data '{"task": {"summary": "新标题"}, "update_fields": ["summary"]}'
```

### 创建任务

```bash
# --assignee 必须，否则用户在飞书看不到任务
lark-cli task +create --summary "任务标题" --due "+2d" --assignee <open_id>
```

### 搜索任务

```bash
lark-cli task +search --query "关键词" --page-all --page-limit 40 --format json
```

## 云空间操作

### 上传文件

```bash
cd /to/directory
lark-cli drive +upload --file ./filename.txt --name "标题.txt"
```

### 列出文件夹内容

```bash
lark-cli drive +list --folder-token FOLDER_TOKEN
```

### 下载文件

```bash
lark-cli drive +download --file-token FILE_TOKEN --output /tmp/save.txt
```

## 已知坑点

| 场景 | 错误现象 | 解法 |
|------|---------|------|
| 日历删除 | missing required path parameter: calendar_id | 用 `--params '{"calendar_id":"...","event_id":"..."}'` |
| 文档更新 | --mode is required | 必须加 `--mode overwrite` 或 `append` |
| drive upload | unsafe file path | 用相对路径，cd 到目标目录执行 |
