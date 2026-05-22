# Drive 文档幂等查重（2026-05-22 实测经验）

## 核心问题

在文件夹内查找或创建「当天复盘总结」文档时，错误做法会导致重复文档堆积：
- 错误做法：用 `docs +search`（全局搜索）按文件名查 → 命中第一个就 break → 可能更新了同名但不同文件夹的旧文档
- 正确做法：用 `drive files list` 列出目标文件夹，按 `created_time` 降序取最新

## 根因

**`docs +search` 是全局搜索**，不认 `--folder-token` 参数（该参数在 `+search` 子命令中不存在）。搜出来的是全云空间匹配结果，不是目标文件夹内的文档。

## 正确做法

### 1. 列出目标文件夹内文件

```bash
lark-cli drive files list \
  --params '{"folder_token": "<folder_token>"}' \
  --format json
```

响应字段（与 search 结果不同）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `token` | string | 文档 token |
| `name` | string | 文件名 |
| `type` | string | `docx` / `doc` / `folder` 等 |
| `created_time` | string | Unix 时间戳（字符串），**注意不是 `create_time`** |
| `modified_time` | string | Unix 时间戳 |
| `parent_token` | string | 父文件夹 token |

### 2. 在结果中按日期筛选 + 按时间降序取最新

```python
def find_doc_in_folder(folder_token: str, date_str: str) -> str | None:
    files = list_folder_files(folder_token)
    matches = []
    for f in files:
        if f.get("type") in ("docx", "doc"):
            name = f.get("name", "")
            if date_str in name:
                ct = int(f.get("created_time", 0))  # 注意：字段名是 created_time
                matches.append((ct, f.get("token"), name))
    if not matches:
        return None
    matches.sort(key=lambda x: x[0], reverse=True)  # 降序
    return matches[0][1]  # 返回最新创建的文档 token
```

### 3. 幂等判断逻辑

```
if doc_id is None:
    # 不存在 → 创建新文档
    create_doc(...)
else:
    # 已存在 → 更新现有文档（始终覆盖）
    update_doc(doc_id, content)
```

## 踩坑记录

| 日期 | 现象 | 原因 | 修复 |
|------|------|------|------|
| 2026-05-22 | 搜索到同名文档但更新了错误的文档 | `docs +search` 是全局搜索，不按 folder 过滤 | 改用 `drive files list` |
| 2026-05-22 | 按 `create_time` 排序取不到真实时间 | 字段名错误，drive API 返回的是 `created_time` 不是 `create_time` | 改为 `int(f.get("created_time", 0))` |
| 2026-05-22 | 命中第一个（最早的）而非最新的 | 只 break 取第一个，未按时间排序 | 按 `created_time` 降序后取 `[0]` |

## 文件夹路径注意

某些文件夹不在根目录，需要传入 `parent_token`：

```python
HERMES_PARENT_TOKEN = "nodcnu9wxEkxzgM53MYnlJXM4Kp"  # hermesAgent 的父文件夹
get_folder_token("HermesAgent", HERMES_PARENT_TOKEN)
```

直接搜索根目录会漏掉嵌套文件夹里的内容。
