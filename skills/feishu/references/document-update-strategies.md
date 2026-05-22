# Document Update Strategies

## The Problem

`lark-cli docs +update --doc DOC_ID --mode append` **appends** content to the existing document. 
Each call adds new blocks at the end, causing version numbers to balloon and content to accumulate.
This is NOT an update — it's an append.

## Correct Approaches

### Full Replacement

```bash
lark-cli docs +update DOC_ID \
  --mode overwrite \
  --markdown-file /tmp/content.md \
  --user-access-token TOKEN
```

This completely replaces all blocks with the new content. Document version resets cleanly.

### Partial Update (Replace a Section)

```bash
lark-cli docs +update DOC_ID \
  --mode replace_range \
  --selection-by-title "## 章节标题" \
  --markdown "## 新标题\n\n新内容" \
  --user-access-token TOKEN
```

This replaces only a specific section by its title. Useful for targeted edits.

### Other Modes

| Mode | Description |
|------|-------------|
| `append` | Add to end (same as import --document-id) |
| `overwrite` | Full replacement — use this for full updates |
| `replace_range` | Replace by title or content range |
| `replace_all` | Search-and-replace all matches |
| `insert_before` / `insert_after` | Insert relative to a title |
| `delete_range` | Remove section by title |

## When to Create a New Document vs. Update

- **Create new**: First time writing content, or when the old doc is badly broken (version > 1000+).
- **Update existing**: Making a correction, adding a section, or refreshing content.

When creating a new doc for the same purpose, delete the old one afterward:

```bash
# Delete with user_access_token (needs drive:drive scope)
curl -X DELETE "https://open.feishu.cn/open-apis/drive/v1/files/DOC_ID?type=docx" \
  -H "Authorization: Bearer {USER_TOKEN}"
```

## ⚠️ 表格内文本更新 — 特殊处理

`content-update --selection-with-ellipsis` **无法匹配表格内的文本块**。这是因为表格单元格 (block_type=32) 是独立的容器块，其子文本块 (block_type=2) 在文档块树中层级不同，selection 算法无法直接定位。

**症状：** 执行 `content-update --mode replace_range --selection-with-ellipsis "文本内容..."` 时报错 "未找到包含起始文本的块"，即使文本确实存在于文档中。

**解决方法：** 改用 `doc update` 按 block ID 精确更新：

```bash
# 1. 获取所有块找到目标文本的 block_id
lark-cli docs +fetch DOC_ID --output json

# 2. 定位到表格单元格内的文本块（type=2 的子块，parent 是 type=32 的单元格）

# 3. 更新该文本块
lark-cli docs +update DOC_ID BLOCK_ID \
  --content '{"update_text_elements":{"elements":[{"text_run":{"content":"新内容"}}]}}'
```

**判定方法：** 查看 `doc blocks` 输出，如果目标文本的 parent_id 指向一个 type=32 的 table_cell 块，则它在表格内，必须用此方法。

## ⚠️ 关键前提：FILE 类型文件无法 content-update

**FILE（.md/.txt 等云盘文件）≠ 飞书原生文档（DOCX）**

只有 **DOCX**（飞书原生文档）才支持 `doc content-update` 系列操作。`.md` 文件（Drive FILE 类型）只能通过删除重建来更新。

| 文件类型 | content-update | drive push --if-exists | 正确更新方式 |
|----------|---------------|------------------------|-------------|
| DOCX（飞书文档） | ✅ 支持 | ✅ 有效 | `doc content-update --mode overwrite` |
| FILE（.md 云盘文件） | ❌ 报错 1770002 | ❌ **有 bug，不生效** | 删除重建或转 DOCX |

### drive push --if-exists overwrite 的已知 bug

`lark-cli drive +upload (overwrites correctly)` 报告 "上传: 1" 但实际上 **不会覆盖同名 FILE 文件**。这是工具 bug，无法通过命令行参数绕过。

**解法：**
1. 直接创建 DOCX 并写入内容（绕过 FILE 类型）
2. 用 API 直接创建在目标文件夹（`POST /docx/v1/documents` + `folder_id`）
3. 后续更新统一用 `doc content-update --mode overwrite`

### FILE 转 DOCX 的标准流程

当需要更新已存在的 .md 文件时，正确的重建流程：

```bash
# 1. 用 API 直接在目标文件夹创建 DOCX
DOC_ID=$(curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"文档标题\",\"folder_id\":\"$FOLDER_TOKEN\"}" | jq -r '.data.document.document_id')

# 2. 写入内容
lark-cli docs +update $DOC_ID --mode overwrite --markdown-file ./content.md \
  --user-access-token $USER_TOKEN
```

### Pure User Identity Mode（应用权限撤销后）

撤销应用授权后，需从旧 CLI 配置中移除 `app_id`/`app_secret`：

```bash
# ~/.lark-cli/ 移除 app_id/app_secret 两行，保留 base_url 等基础配置
# 之后所有 lark-cli 调用默认走 user_access_token
```

**重要**：无 `app_id`/`app_secret` 时，lark-cli 默认就是 user identity。对用户云盘文件操作必须加 `--user-access-token $USER_TOKEN`。

## Why This Happens

`lark-cli docs +update --mode append` was designed for initial import. The `--document-id` flag lets you re-import to the same doc for retry purposes, but it doesn't clear existing content. For updates, always use `doc content-update --mode overwrite`.
