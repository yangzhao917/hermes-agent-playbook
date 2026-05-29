# AgentOS 注意力治理 MVP 落地记录

更新时间：2026-05-29

## 1. 当前结论

AgentOS 主线治理已从旧的工程状态模型升级为注意力治理模型。

旧模型：

```text
now / next / later / paused / archived
```

新模型：

```text
committed / maintain / incubate / waiting / delegated / archived
```

用户侧不暴露工程字段，默认使用自然语言：

```text
今天真正要推进的 / 先别掉线的 / 先攒着的 / 等反馈的 / 已经交给别人处理的 / 已结束的
```

核心产品原则：

- 微信 Clawbot 是决策、确认、纠偏入口。
- 飞书是事实档案和复盘追溯层。
- YAML 是当前主线运行态。
- audit jsonl 是轻量 ActionLog。
- 复盘从“信息总结”升级为“注意力收口”。
- 周复盘等于“本周事实 + 下周取舍”。
- 没有证据，不做强判断。

## 2. 远端落地状态

已完成：

- 运行态主线文件升级到 v2：`~/.hermes/state/agentos/mainlines.yaml`
- `mainline-governance` skill 升级到 v2。
- 晨间提醒读取 `mode/user_label/current_stage`。
- 每日复盘输出“注意力收口 + 飞书事实档案”。
- 每周复盘输出“本周事实 + 下周取舍”。
- `personal-os-roles` 去除固定五条主线心智，改为读取 YAML v2。
- 旧 `hermes-agent-playbook` repo skill 内容改为 `agent-os-repo` 规则。
- AgentOS 产品仓库正式路径改为 `~/.hermes/agent-os`。
- 旧路径保留 symlink：`~/.hermes/hermes-agent-playbook -> ~/.hermes/agent-os`。
- `update-status` 保留为 deprecated alias，避免旧调用断裂；新命令使用 `update-mode`。

不做：

- 不修改 Hermes core。
- 不新增 SQLite。
- 不新增 Dashboard。
- 不新增健康、睡眠、财务、微信聊天数据源。
- 不自动写长期记忆。

## 3. 当前主线配置

| 主线 | mode | 用户表达 | 当前阶段 |
| --- | --- | --- | --- |
| Hermes / AgentOS 系统建设 | `committed` | 今天真正要推进的 | 跑通主线治理 MVP |
| AI Agent 求职 | `committed` | 今天真正要推进的 | 明确可投递材料和机会推进 |
| 小红书个人品牌 | `incubate` | 先攒着的 | 试运行 AgentOS 内容方向 |
| 健康、睡眠、财务和生活质量 | `maintain` | 先别掉线的 | 数据接入前低频检查 |
| 十堰黑客松社区轻运营 | `delegated` | 已经交给别人处理的 | 李国正负责日常宣发，仅保留升级提醒 |

十堰黑客松只在这些条件出现时提醒：

```text
关键资源、重要合作、固定活动节点、舆情或声誉风险、李国正请求支持、必须由杨钊决策。
```

## 4. 数据模型

状态文件：

```text
~/.hermes/state/agentos/mainlines.yaml
```

示例：

```yaml
version: 2
mainlines:
  - id: hermes-agentos
    name: Hermes / AgentOS 系统建设
    mode: committed
    user_label: 今天真正要推进的
    objective: 把 Hermes、skills、飞书、微信读书、ima 和个人数据源升级为 AgentOS 产品原型
    current_stage:
      name: 跑通主线治理 MVP
      review_at: "2026-06-02"
      done_when:
        - 早上能帮你收口今天真正要推进的事
        - 晚上能判断今天有没有真实推进
        - 周末能用本周事实整理下周取舍
        - 你能在微信里纠正它
      acceptance_evidence:
        - morning reminder generated with attention summary
        - daily review generated with attention closure
        - weekly review generated with next-week tradeoff plan
        - user correction handled through Clawbot
```

## 5. Skill 接口

主脚本：

```text
~/.hermes/skills/mainline-governance/scripts/mainlines.py
```

命令：

```bash
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py list
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py classify "整理 AgentOS PRD"
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py suggest-review
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py update-mode xiaohongshu-brand committed --reason "本周有明确发布窗口"
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py update-stage hermes-agentos --name "跑通主线治理 MVP" --review-at 2026-06-02
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py correction --text "这不是小红书，是 AgentOS"
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py undo-last
```

输出统一包含：

```json
{
  "ok": true,
  "facts": [],
  "inferences": [],
  "uncertainties": [],
  "recommendations": [],
  "requires_confirmation": false
}
```

## 6. 纠偏协议

| 用户表达 | 处理 |
| --- | --- |
| 这不是小红书，是 AgentOS | 当前归类纠偏，写 audit，不写长期偏好 |
| 这周先别管小红书 | 本周临时降噪，不写长期偏好 |
| 以后小红书只在有发布窗口时提醒 | 长期偏好候选，需要确认 |
| 把这个交给李国正 | 委托候选，需要确认 |
| 这个结束了 | 归档候选，需要确认 |
| 撤销刚才的调整 | 回滚最近一次 `update-mode` |

高影响动作必须确认：

- 改 `mode`
- 改当前阶段
- 归档
- 委托
- 写长期偏好
- 写长期记忆

## 7. 防幻读规则

- 事实、判断、不确定必须分开。
- 关键词命中只算候选证据，不等于真实推进。
- 缺健康、睡眠、财务、微信聊天数据时必须明说缺数据。
- 临时表达不能自动变成长期偏好。
- 每条建议必须有依据。
- 每日复盘不自动写长期记忆，只生成候选。

## 8. 复盘结构

每日微信摘要：

```text
今天真正推进了：
明天建议只抓：
先不用花力气：
需要你确认：
我不确定的部分：
```

每日飞书文档：

```text
注意力收口
完整事实记录
主线证据候选
输入与长期记忆候选
数据质量说明
```

周复盘：

```text
本周真正推进了：
下周建议只抓：
先不用花力气：
需要确认：
完整复盘已写入飞书。
```

## 9. 验证结果

已通过：

```bash
python3 -m py_compile \
  ~/.hermes/skills/mainline-governance/scripts/mainlines.py \
  ~/.hermes/scripts/morning_reminder.py \
  ~/.hermes/skills/morning-reminder/scripts/morning_reminder.py \
  ~/.hermes/skills/daily-review/scripts/daily_review.py \
  ~/.hermes/skills/weekly-review/scripts/weekly_review.py
```

已验证：

- `mainlines.py list` 输出 `mode/user_label/current_stage`
- `classify "整理 AgentOS PRD"` 命中 AgentOS
- `classify "十堰黑客松宣发排期"` 不建议日常执行
- `correction --text "这不是小红书，是 AgentOS"` 输出低影响纠偏
- `suggest-review` 输出 `update-mode` 建议，不再使用旧状态作为产品语言
- 晨间提醒按注意力收口输出
- 每日复盘区分事实、判断、不确定
- 周复盘包含本周事实和下周取舍

## 10. 兼容说明

- 旧 repo 路径只作为 symlink 保留。
- 旧 `update-status` 只作为 deprecated alias 保留。
- weekly-review 会兼容读取旧飞书文档中的“五条主线推进”章节，但新文档写“主线证据候选”。
