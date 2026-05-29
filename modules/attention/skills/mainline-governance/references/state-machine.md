# AgentOS Attention Mode State Machine

Allowed modes:

- `committed`: 今天真正要推进的。Default source for daily focus.
- `maintain`: 先别掉线的。Only surface for anomaly, periodic check, or explicit task.
- `incubate`: 先攒着的。Collect input and opportunities; do not force action.
- `waiting`: 等反馈的。Surface when due, overdue, or external feedback appears.
- `delegated`: 已经交给别人处理的。Escalation only.
- `archived`: 已结束的。Historical context only.

Preferred lifecycle:

```text
create -> incubate/maintain -> committed -> maintain/incubate/waiting/delegated -> archived
```

Mainlines do not directly "complete". Current stages are reviewed instead.

Anti-hallucination rules:

- Facts, inferences, and uncertainties must be separated.
- Missing data must be named as missing.
- Keyword matches are candidate evidence only.
- Temporary corrections must not become long-term preferences without confirmation.
- High-impact writes require confirmation and an audit log entry.
