---
name: agent-os-repo
description: AgentOS repository management rules. Use when syncing Hermes runtime skills and docs into Yang Zhao's AgentOS product repository at ~/.hermes/agent-os, checking repo status, preparing diffs, or preparing commits. Runtime skills remain the execution source of truth unless the user asks to sync.
version: 3.0.0
category: productivity
---

# AgentOS Repo

## Repository

- Product name: AgentOS
- Local product repository: `~/.hermes/agent-os`
- Legacy compatibility path: `~/.hermes/hermes-agent-playbook -> ~/.hermes/agent-os`
- Remote: `https://github.com/yangzhao917/AgentOS`
- Branch: `main`

## Source Of Truth

- Runtime skills live in `~/.hermes/skills/`.
- The product repository stores product docs, synced skills, runtime mappings, and implementation assets.
- Runtime state, logs, tokens, and personal data must not be committed.
- Do not commit or push automatically. Prepare diffs first and wait for Yang's confirmation.

## Repository Organization

AgentOS is organized by product capability, not by raw skill type:

```text
docs/           Product, architecture, and operations docs
interfaces/     WeChat, Feishu docs, and CLI entry points
modules/        Attention, execution, knowledge, discovery, and personal modules
integrations/   Data-source plans and connector notes
runtime/        Hermes runtime mappings and examples
manifests/      Skill sync inventory
vendor/         External skills and upstream dependencies
```

## Sync Rules

- Prefer syncing from runtime to repo, because runtime is what Hermes actually uses.
- Record every runtime-to-repo path in `runtime/mappings/runtime-to-repo.yaml`.
- Record ownership and module role in `manifests/skills.yaml`.
- Keep the legacy name `hermes-agent-playbook` only as a compatibility path, not as a product name.

## Checks Before Commit

```bash
git status --short
git diff --stat
python3 -m py_compile \
  ~/.hermes/skills/mainline-governance/scripts/mainlines.py \
  ~/.hermes/scripts/morning_reminder.py \
  ~/.hermes/skills/daily-review/scripts/daily_review.py \
  ~/.hermes/skills/weekly-review/scripts/weekly_review.py
```
