# AgentOS

AgentOS 是杨钊的个人操作系统：通过微信对话收口注意力，用飞书沉淀事实档案，用 Hermes skills 执行具体动作，并逐步接入个人数据源。

## 产品定位

AgentOS 当前最重要的目标不是“帮你做更多事”，而是每天帮你回答五个问题：

- 今天真正应该抓什么？
- 今天到底有没有真实推进？
- 哪些事情先不用花力气？
- 哪些动作必须先问你确认？
- 哪些事实值得沉淀，方便之后复盘？

## 当前 MVP

```text
微信 Clawbot = 对话、确认、纠偏入口
飞书 = 日程、任务、事实档案
YAML = 当前注意力主线状态
Hermes skills = 执行层和数据连接器
audit jsonl = 轻量 ActionLog
```

当前 MVP 不修改 Hermes core，不新增数据库，不提交真实运行态 state、日志、token 或个人隐私数据。

## 仓库结构

```text
docs/           产品、架构和运维文档
interfaces/     用户入口：微信、飞书文档、CLI
modules/        AgentOS 产品能力模块
integrations/   数据源接入计划和连接器说明
runtime/        Hermes 运行态映射和示例
manifests/      skill 同步清单
vendor/         外部依赖和上游 skill
```

## 产品模块

| 模块 | 作用 | 关键 skills |
| --- | --- | --- |
| `attention` | 判断什么值得注意，并完成每日/每周闭环 | `mainline-governance`, `morning-reminder`, `daily-review`, `weekly-review` |
| `execution` | 把决定落到日程和任务 | `feishu-calendar`, `feishu-task` |
| `knowledge` | 接入阅读、笔记和飞书内容 | `weread`, `ima-skill`, `lark-cli` |
| `discovery` | 收集外部信号和内容素材 | 网络搜索、公众号、小红书、黑客松搜索 |
| `personal` | 个人辅助工作流 | `friend-social-review`, `memory-cleanup` |

## 运行态模型

产品仓库不是运行态真源。Hermes 实际运行文件在腾讯云服务器：

```text
~/.hermes/skills/                 运行态 skills
~/.hermes/scripts/                cron wrapper
~/.hermes/state/agentos/          运行态状态
~/.hermes/logs/agentos/           audit 日志
~/.hermes/agent-os/               产品仓库
```

用 `manifests/skills.yaml` 和 `runtime/mappings/runtime-to-repo.yaml` 追踪运行态 skill 和仓库模块之间的映射。

## 防幻读和确认规则

- 事实、判断、不确定和建议必须分开。
- 健康、睡眠、财务、微信聊天数据未接入时，必须明确说缺数据。
- 低影响纠偏可以写入 audit。
- 高影响动作必须让用户确认，包括改主线、改阶段、归档、委托、写长期记忆、对外动作。
- 飞书是事实档案，微信是确认和纠偏入口。

## 当前状态

这个仓库正在从 Hermes skills 集合重构为 AgentOS 产品仓库。当前刻意保持 MVP 形态：不做 dashboard、不做安装器、不加数据库，也不改 Hermes core。
