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

### friend-social-review

**功能**：以朋友口吻帮你复盘人际关系中的纠结事。不讲大道理，直接说人话。融合 5 本经典人际著作的底层逻辑，一对一交友场景的实战复盘。

**定位**：不是专家/老师/心理医生，而是站在你这边帮你分析的朋友。直接给结论，不展开推理，不给背景说明。如果太敏感、太上头、投入太多，会直接说。

**触发**：用户描述一段关系里的经历，请求分析时自动加载。

**文件**：`技能管理/skills/friend-social-review/`

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
