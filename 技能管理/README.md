# 技能管理

> Skill 评估原则与安装管理

## 技能评估原则

- **不能仅凭名字/描述判断冗余**：需加载实际内容后再下结论
- **技能不占空间**：不确定时留着比删了好
- **沉淀标准**：以一周为窗口，重复多次 + 复用价值（对自己和他人都有意义）→ 沉淀为技能

## Skill 目录

用户 Skills：`~/.hermes/skills/`
内置 Skills：`~/.hermes/hermes-agent/skills/`

## 用户创建技能

存放在 `技能管理/skills/` 目录下，随本手册一并维护。

| 技能 | 功能 | 触发场景 | 文件 |
|------|------|----------|------|
| feishu-task | 飞书任务 CRUD + 逾期预警 + 统计概览 | 用户请求查看/创建/完成飞书任务 | [skills/feishu-task/](skills/feishu-task/) |
| friend-social-review | 以朋友口吻复盘人际关系纠结事 | 用户描述关系经历并请求分析 | [skills/friend-social-review/](skills/friend-social-review/) |
| daily-review | 每日复盘总结生成与管理 | 「写复盘」「生成复盘」「今日总结」 | [skills/daily-review.md](skills/daily-review.md) |
| morning-reminder | 每日晨间日程提醒（7:00） | cron 自动触发、用户问「今天有什么安排」 | [skills/morning-reminder.md](skills/morning-reminder.md) |

## 推荐开源技能

| 技能 | 来源 | 用途 | 开源链接 |
|------|------|------|----------|
| lark-cli | @larksuite/cli | 飞书文档/日历/任务/云空间全部操作 | https://github.com/larksuite/cli |
| just-one-api | 开源项目 | 小红书、抖音、微博数据查询 | https://github.com/RIM99/just-one-api |
| web-search-ex-skill | @yejinlei | 多引擎搜索（百度/必应/DuckDuckGo） | https://github.com/yejinlei/web-search-ex-skill |
| yuanbao | 开源项目 | 元宝群组管理 | - |
| mmx-cli | MiniMax | MiniMax 文本/图片/视频/语音生成 | https://github.com/MiniMax-api/minimax-cli |
| weread | 开源项目 | 微信读书助手 | - |
| humanizer / de-ai-ify | @ieou新知 | 去除 AI 写作痕迹 | https://github.com/ieou/humanizer |
| twitter-playwright-graphql | 开源项目 | X/Twitter GraphQL 自动化 | - |

## Skill 安装

```bash
# 通过 hermes curator 安装
hermes curator install <skill-name>

# 或手动放置到 ~/.hermes/skills/<skill-name>/
```

## Skill 编写规范

触发条件写在 SKILL.md 的 frontmatter 的 `trigger` 字段，格式：

```yaml
---
name: my-skill
trigger: "调用 XXX / 场景描述"
---
```
