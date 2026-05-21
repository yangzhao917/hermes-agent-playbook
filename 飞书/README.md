# 飞书

> 飞书文档、待办、日历的架构规范与操作原则

## 文档统一存放目录

- **HermesAgent**（folder_token: `<FOLDER_TOKEN>`）
- 所有 AI 创建的文档统一放这里
- 子目录结构按需创建（每日复盘/项目/知识沉淀等）

## 待办任务

统一用 `feishu-task` skill：

```bash
python3 /home/ubuntu/skills/feishu-task/scripts/list_tasks.py --completed=false
python3 /home/ubuntu/skills/feishu-task/scripts/create_task.py --summary "标题" --due "+2d"
python3 /home/ubuntu/skills/feishu-task/scripts/complete_task.py --query "关键词"
python3 /home/ubuntu/skills/feishu-task/scripts/stats.py
```

具体命令见 `lark-cli` skill 和 `feishu-task` skill。

> ⚠️ 任务创建必须带 `--assignee`，否则用户在飞书看不到任务

> ⚠️ 日历查询用 `lark-cli calendar +agenda`（今天默认），不要用 `+events`

## 日程与待办联动规则

**新增 / 更新 / 完成 / 删除 时，日程和待办必须同步处理。**

- 新增：同时创建日程 + 待办，执行人/参与人一致
- 更新：同时更新时间
- 完成：同时标记完成（或只留一种）
- 删除：同时删除

## 去重原则

日程、待办、文档同一主题保留最新一条，旧的一律删除或归档。

- **日程**：同标题同时段 → 保留一条
- **待办**：同主题 → 保留最新，删旧
- **文档**：同标题或实质同内容 → 保留最新

## Token 管理

- Token 文件：`~/.lark-cli/hermes`
- access_token：2 小时有效期
- refresh_token：7 天有效期
- lark-cli 自动续期，无需手动刷新
- **7天内不要主动要求用户重新扫码授权**，除非 token 明确失效报错

### 常见错误码

| 错误码 | 含义 | 处理 |
|--------|------|------|
| 99991677 | access_token 过期 | 重新 `lark-cli auth login` |
| 20025 | App ID/Secret 缺失 | 检查 .env 文件 |
| 20026 | refresh_token 过期 | 需重新 Device Flow 授权 |
| 193003 | 事件已删除 | 忽略（幂等） |
| 191002 | calendar 无 writer 角色 | 换用户 token |

## 具体命令

所有具体操作命令见 `lark-cli` skill（`skill_view lark-cli`）和 `feishu-task` skill（`skill_view feishu-task`）。

## 横向规范

- [定时任务规范](../定时任务/README.md)
- [用户偏好](../用户规约/README.md)
- [环境配置](../配置指南/README.md)
