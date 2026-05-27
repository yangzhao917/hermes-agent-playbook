# 默认环境变量说明

以下非敏感配置已在 `scripts/wechat_official_client.py` 中内置默认值，不配置环境变量也会自动使用：

```bash
JUSTONE_API_BASE_URL=https://api.justoneapi.com
JUSTONE_TIMEOUT=75
JUSTONE_MAX_RETRIES=1
JUSTONE_DETAIL_MIN_INTERVAL_SECONDS=8
JUSTONE_DETAIL_CACHE_TTL_SECONDS=604800
JUSTONE_SEARCH_CACHE_TTL_SECONDS=21600
JUSTONE_CACHE_DIR=.cache/justone_wechat
```

Token 不写死默认值。请求时只读取：

```text
JUSTONE_API_TOKEN
```

如果没有配置 Token，脚本会直接报错退出，避免模型在无数据时继续生成结论。
