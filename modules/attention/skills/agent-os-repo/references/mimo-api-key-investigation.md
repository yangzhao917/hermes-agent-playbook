# Mimo / Xiaomi API Key Investigation Notes (2026-05-29)

## Key Format: `tp-` Prefix = Invalid

All `tp-` prefixed Xiaomi MiMo / token-plan keys returned `401 Invalid API Key` against all tested endpoints:
- `https://api.xiaomimimo.com/v1/...`
- `https://token-plan-cn.xiaomimimo.com/anthropic/v1/...`

**All 39 keys tested — 0% valid.**

This format may be deprecated or tied to a specific billing plan that's been deactivated.

## Active Runtime Key Chain

```bash
# Current env vars (XIAOMICODING_API_KEY = <redacted>, INVALID)
env | grep XIAOMICODING_API_KEY

# Actual gateway process env
cat /proc/$(pgrep -f 'hermes_cli.main gateway')/environ | tr '\0' '\n' | grep XIAOMI

# Provider source — which env var does it read?
cat ~/.hermes/hermes-agent/plugins/model-providers/xiaomi/__init__.py
# → reads XIAOMI_API_KEY, base_url = https://api.xiaomimimo.com/v1

# Custom provider config (yaml-based, overrides provider plugin)
grep -A5 'custom:xiaomicoding' ~/.hermes/config.yaml
# → provider: custom:xiaomicoding, api_key: <redacted>, INVALID
```

## Critical Discovery: Mimo Fallback Active

When Mimo API key is invalid, Hermes falls back to `minimax-cn` (MiniMax CN API key redacted).

**This session is running on MiniMax-CN, NOT actual Mimo.**

To check which provider is actually serving:
```bash
grep -A2 'fallback_providers' ~/.hermes/config.yaml
```

## Investigation Pattern (for future API key validation)

When validating API keys:

1. **Start with env vars** — `env | grep -i 'KEY\|TOKEN'`
2. **Check the target process** — `cat /proc/$(pgrep -f 'gateway')/environ`
3. **Read provider source** — which exact env var does the plugin read?
4. **Try both endpoints** — Xiaomi uses different base URLs for different products
5. **Check fallback chain** — if primary fails, what does it fall back to?
6. **Distinguish "this session works" from "key is valid"** — the session working doesn't mean the key in config is valid

## Xiaomi Provider Env Vars

| Provider | Env Var | Base URL |
|----------|---------|----------|
| xiaomi (plugin) | `XIAOMI_API_KEY` | `https://api.xiaomimimo.com/v1` |
| xiaomicoding (custom, yaml) | `XIAOMICODING_API_KEY` | `https://token-plan-cn.xiaomimimo.com/anthropic` |

The two providers read different env vars and hit different endpoints.
