---
name: mainline-governance
description: Use when managing Yang Zhao's AgentOS attention mainlines: list, classify, diagnose, correct, update modes/stages, archive, merge, and prepare review suggestions with anti-hallucination guardrails.
version: 2.0.0
author: 杨钊
license: MIT
metadata:
  hermes:
    tags: [agentos, mainlines, attention, review, governance]
    related_skills: [personal-os-roles, morning-reminder, daily-review, weekly-review]
    requires_toolsets: [terminal]
---

# mainline-governance

Dynamic attention governance for Yang Zhao's AgentOS on Hermes.

## Use When

- Listing current AgentOS attention mainlines.
- Classifying a task, calendar event, review item, or message into a mainline.
- Handling Clawbot correction text such as "这不是小红书，是 AgentOS" or "这周先别管小红书".
- Creating, archiving, merging, deleting mistaken entries, or updating a mainline mode/stage after confirmation.
- Preparing weekly review suggestions based on evidence.

## Runtime State

Runtime state lives outside the skill so skill updates do not overwrite it:

```text
~/.hermes/state/agentos/mainlines.yaml
```

Audit log:

```text
~/.hermes/logs/agentos/mainline_events.jsonl
```

## User Language

Do not expose engineering terms to Yang by default. Prefer:

- 今天真正要推进的
- 先别掉线的
- 先攒着的
- 等反馈的
- 已经交给别人处理的
- 已结束的

Internal `mode` values:

- `committed`
- `maintain`
- `incubate`
- `waiting`
- `delegated`
- `archived`

## Commands

```bash
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py list
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py classify "整理 AgentOS PRD"
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py suggest-review
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py update-mode xiaohongshu-brand committed --reason "本周有明确发布窗口"
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py update-stage hermes-agentos --name "跑通主线治理 MVP" --review-at 2026-06-02
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py correction --text "这不是小红书，是 AgentOS"
python3 ~/.hermes/skills/mainline-governance/scripts/mainlines.py undo-last
```

`update-status` is kept only as a deprecated compatibility alias. New work should use `update-mode`.

## Rules

- Default to 2 committed mainlines; allow at most 3 with a clear reason.
- `committed` can enter daily focus.
- `maintain`, `incubate`, `waiting`, and `delegated` should not manufacture daily tasks.
- `delegated` only surfaces when escalation conditions are met.
- Default to archive rather than delete. Use delete only for mistaken or duplicate entries.
- High-impact changes require Yang's confirmation.
- Do not infer unavailable health, sleep, finance, or WeChat chat data.
- Separate facts, inferences, and uncertainties.
- Keyword matches are candidates, not proof of real progress.

## Current Personal Constraint

十堰黑客松社区日常宣发已授权给联合发起人李国正。Only escalate for key resources, important cooperation, fixed event milestones, public reputation risk, Li Guozheng asking for support, or decisions requiring Yang.
