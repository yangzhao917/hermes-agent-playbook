# 技能管理

> Skill 评估原则与安装管理

## 技能评估原则

- **不能仅凭名字/描述判断冗余**：需加载实际内容后再下结论
- **技能不占空间**：不确定时留着比删了好
- **沉淀标准**：以一周为窗口，重复多次 + 复用价值（对自己和他人都有意义）→ 沉淀为技能

## Skill 目录

用户 Skills：`~/.hermes/skills/`
内置 Skills：`~/.hermes/hermes-agent/skills/`

## 推荐技能清单

| 技能 | 用途 |
|------|------|
| lark-cli | 飞书文档/日历/任务/云空间全部操作 |
| just-one-api | 小红书、抖音、微博数据查询 |
| web-search-ex-skill | 多引擎搜索（百度/必应/DuckDuckGo） |
| friend-social-review | 人际关系辅助分析 |
| yuanbao | 元宝群组管理 |
| mmx-cli | MiniMax 文本/图片/视频/语音生成 |
| weread | 微信读书助手 |
| humanizer / de-ai-ify | 去除 AI 写作痕迹 |
| twitter-playwright-graphql | X/Twitter 自动化 |

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
