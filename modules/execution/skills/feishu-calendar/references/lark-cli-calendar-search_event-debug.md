# 飞书日历 search_event 调试记录

## 问题现象

调用 `lark-cli calendar events search_event` 反复报错：
- `missing required path parameter: calendar_id`
- `query is required`

即使传入 `--calendar-id`、`--params '{"calendar_id":...}'`、`--data '{"query":...}'` 均无效。

## 根因

`search_event` 是路径参数（path parameter），不是 body 也不是 query 参数。
`calendar_id` 必须同时作为**位置参数**（lark-cli 命令行的字面量路径）和 `--params` JSON 里的字段，`query` 必须放在 `--data` JSON 里。

## 正确命令格式

```bash
/usr/lib/node_modules/@larksuite/cli/bin/lark-cli calendar events search_event \
  "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn" \
  --params '{"calendar_id": "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn"}' \
  --data '{"query":"CSS播客"}'
```

三个要素缺一不可：
1. **位置参数**：`"日历ID"` 作为命令行的第一个字面量
2. `--params`：JSON 里放 `calendar_id` 字段
3. `--data`：JSON 里放 `query` 字段

## 验证

2026-05-27 实测成功，返回：
```json
{"code": 0, "data": {"items": [{"meta_data": {"summary": "CSS播客重录", ...}}]}}
```

## 相关 CLI 路径

lark-cli 安装在：`/usr/lib/node_modules/@larksuite/cli/bin/lark-cli`（Go 二进制，非 Node.js）