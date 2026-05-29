# lark-cli JSON 输出格式与解析规范

## 发现时间
2026-05-22（杨钊 session）

## 背景
`lark-cli <module> <command> --format json` 的输出格式并不统一，解析器如果按 `\n` 逐行解析会全部失败。

## 输出格式分类

| 命令示例 | 输出格式 | 正确解析方式 |
|----------|----------|--------------|
| `calendar events instance_view --format json` | **多行格式化 JSON**（68行，缩进+换行） | 整段 `json.loads(stdout)` |
| `task tasks list --format json` | **紧凑单行 JSON** | 整段 `json.loads(stdout)` |
| `docs +fetch --format json` | 含 `[deprecated]` 前缀行 | 跳过前缀，`find('{')` 后整段解析 |
| `task +create --format json` | 含 `[deprecated]` 前缀行 | 同上 |

## 错误解析模式（已踩坑）

```python
# ❌ 错误：逐行解析多行格式化 JSON
def _parse_json_bad(stdout):
    for line in stdout.strip().split("\n"):
        try:
            return json.loads(line)  # 每行都不是完整 JSON，全失败
        except:
            continue
    return None
```

## 正确解析模式

```python
def _parse_json(stdout):
    text = stdout.strip()
    if not text:
        return None
    # 策略一：直接解析整段（处理多行格式 JSON）
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 策略二：跳过前缀行，找第一个 { 开始解析
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("[") or line == "}":
            continue
        try:
            brace_start = line.find("{")
            if brace_start >= 0:
                return json.loads(line[brace_start:])
        except json.JSONDecodeError:
            continue
    return None
```

## 受影响命令（已验证）

| 命令 | 格式类型 |
|------|---------|
| `calendar events instance_view --format json` | 多行格式化 |
| `calendar events get --format json` | 多行格式化 |
| `calendar +create --format json` | 多行格式化 |
| `task tasks list --format json` | 紧凑单行 |
| `task +create --format json` | 含前缀 |
| `task +complete --format json` | 含前缀 |
| `task +search --format json` | 含前缀 |
| `docs +fetch --format json` | 含前缀 |

## 通用的 `grep` 判断法（不用解析 JSON）

有时只需要判断成功/失败，不需要解析完整数据：

```bash
# 判断 code=0
echo "$output" | grep -q '"code": 0' && echo "OK" || echo "FAIL"

# 判断 ok=true
echo "$output" | grep -q '"ok": true' && echo "OK" || echo "FAIL"
```

但复杂数据提取必须用 JSON 解析，不能用 grep。
