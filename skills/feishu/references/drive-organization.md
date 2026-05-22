# 飞书云空间文件整理参考

## 用户身份 vs App身份

- 不加 `--user-access-token` → 操作在 app 空间，用户看不见
- 加 `--user-access-token` → 操作在用户个人云空间，用户可见
- `lark-cli drive +list`（无用户token）= app 空间的文件列表
- `file list --user-access-token` 需要 `drive:drive:readonly` scope

## 获取 drive:drive:readonly scope

标准 `lark-cli auth login --domain drive --recommend` 只给 `drive:drive.metadata:readonly`（不够列文件）。必须：

```bash
lark-cli auth login --scope "auth:user.id:read drive:drive:readonly offline_access" --no-wait --json
# 用户扫码后轮询
lark-cli auth login --device-code <code> --json
```

## 文档类型处理

| 类型 | 操作 | 原因 |
|------|------|------|
| 自己的 docx/bitable/sheet | `file move` 移入目录 | 直接挪动文件本身 |
| 他人的 docx/bitable/sheet | `file shortcut` 快捷方式 | 无权移动，只创引用 |
| slides（自己的或他人的） | `file shortcut` 快捷方式 | slides 不支持 `file move` |

## 文件夹创建

```python
TOKEN = json.load(open("/home/ubuntu/.lark-cli/"))["access_token"]
UA = f'--user-access-token "{TOKEN}"'

# 创建顶级文件夹
lark-cli drive +mkdir "文件夹名" {UA} --output json

# 创建子文件夹
lark-cli drive +mkdir "子文件夹" --parent <parent_token> {UA} --output json
```

## 删除文件夹

```bash
echo y | lark-cli drive +delete <folder_token> --type folder --user-access-token "$TOKEN"
```

## 搜索文档

用 app token（无 `--user-access-token`）搜到的结果更多，但可能包含不在用户空间的内容。用 user token 搜到的结果是用户真实可见的文档列表。

```bash
# app token 搜索（范围更广）
lark-cli docs +search "" --count 50

# user token 搜索（只返回用户空间可见的）
lark-cli docs +search "" --count 50 --user-access-token "$TOKEN"
```

## 用户已有目录的检查

在开始组织之前，先列出用户已有的文件夹/目录结构：
```bash
lark-cli drive +list --user-access-token "$TOKEN"
```

如果用户已有 `个人`、`Projects`、`archive` 等文件夹，应该在此基础上整合，而不是另起一套。尊重用户已有的组织习惯。
