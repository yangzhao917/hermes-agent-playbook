# 系统概览

## 概念架构

```text
User
  -> WeChat Clawbot
  -> Hermes agent
  -> AgentOS skills
  -> Feishu / WeRead / ima / other data sources
  -> Feishu factual archive + WeChat confirmation
```

## 分层

| 层级 | 责任 |
| --- | --- |
| Interface | 微信 Clawbot、飞书文档、CLI |
| Product modules | 注意力、执行、知识、发现、个人辅助 |
| Runtime | Hermes skills、scripts、cron、state、logs |
| Data sources | 飞书、微信读书、ima，以及未来健康/睡眠/财务/聊天数据 |
| Governance | 确认规则、audit log、防幻读约束 |

## 运行态状态

运行态状态不提交到仓库。当前注意力主线状态在：

```text
~/.hermes/state/agentos/mainlines.yaml
```

示例 schema 在：

```text
runtime/state/mainlines.example.yaml
```

## 防幻读规则

- 关键词命中只是候选证据，不等于真实推进。
- 缺数据必须直接说明。
- 复盘必须区分事实、判断、不确定和建议。
- 长期变化必须得到用户明确确认。
