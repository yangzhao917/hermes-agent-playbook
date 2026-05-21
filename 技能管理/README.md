# 技能管理

> Skill 评估原则与安装管理

## 技能调用原则

**不需要每次都 load skill**：熟悉稳定的 skill（如 feishu-task）直接调脚本，skill 文档只是参考。

**何时 load skill：**
- 新装的 / 久未用的 skill → 先 `skill_view` 确认参数和坑点
- 复杂操作流程（lark-cli、mmx-cli 等）→ 先加载了解 API 限制再执行
- 纯文档型 skill（friend-social-review、writing-polish 等）→ 需要读逻辑才能做事，必须加载

**防止"我以为我记得"：** 定期核对 skill 文档有没有更新，不确定时先查再执行。

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
| feishu-calendar | 飞书日程查看/创建/删除，支持相对日期快捷方式 | 用户请求查看/创建/删除日历日程 | [skills/feishu-calendar/](skills/feishu-calendar/) |
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

技能存放位置：`HERMES_SKILLS_DIR=/home/ubuntu/skills`（用户 Skills）和 `~/.hermes/skills/`（内置用户 Skills）。

手动放置到 `~/.hermes/skills/<skill-name>/`，Hermes 会自动发现。

```bash
# 安装来自 GitHub/Hub 的技能
hermes skills install <skill-name>

# 技能安装后会被自动发现（skills_list 可查）
```

## Skill 编写规范

触发条件写在 SKILL.md 的 frontmatter 的 `trigger` 字段，格式：

```yaml
---
name: my-skill
trigger: "调用 XXX / 场景描述"
---
```
