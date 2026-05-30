# Discovery Module

发现模块负责收集外部信号和内容素材。

## Skills

- `web-search-ex-skill`
- `hackathon-activity-search`

## 边界

发现结果应尽可能保留来源。缺失字段要标记为未知，不能靠模型经验补全。


## 已清理

- `url-reader`：运行时缺少 Playwright、Firecrawl、bs4，且 CLI 无标准 help；不再作为可用抓取入口。
- `agent-reach`：仅保留过文档，服务器缺少 miku_ai、Camoufox、Playwright 和小红书登录态；已从产品仓库移除。
- `/tmp/xhs-mcp`：临时小红书 MCP 包，缺少 Cookie / xs / xs_common，不能作为稳定数据源；已删除。

- `wechat-official-content-search`：Just One 微信公众号接口当前搜索返回 `COLLECT FAILED`，不能作为稳定数据源；已删除。
- `xiaohongshu-justone-fallback`：Just One 小红书笔记搜索 V2/V3 当前返回 `COLLECT FAILED`，只剩关键词建议可用，不满足数据抓取需求；已删除。
- `just-one-api` vendor 文档：无保留 runtime skill 依赖，且小红书/微信接口当前不满足稳定抓取需求；已删除。
