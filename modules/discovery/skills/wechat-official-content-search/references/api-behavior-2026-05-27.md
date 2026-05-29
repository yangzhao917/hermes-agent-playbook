# 微信公众号接口行为记录（2026-05-27）

## 搜索接口

**状态**: ✅ 正常（`code: 0`）
**接口**: `GET /api/weixin/search/v1`
**token 认证方式**: URL query 参数 `token=xxx`（非 Header）
**注意**: 短时间大量请求可能触发限流

调用示例：
```bash
cd ~/.hermes/skills/wechat-official-content-search
JUSTONE_API_TOKEN="4Qrc10Rcc3rdhFay" \
python scripts/wechat_official_client.py search \
  --keyword "关键词" --offset 0 --search-type _2 --sort-type _2
```

## article_detail 接口

**状态**: ⚠️ 频繁 `COLLECT FAILED`
**含义**: Just One 上游微信采集失败，非接口参数问题
**规律**: 搜索结果多的关键词，对应文章详情更容易失败；换关键词重试可能成功

当 `article_detail` 失败时：
- 改用 `search` 结果中的 title/desc 作为已知信息
- 不要基于失败响应编造正文内容
- 可尝试换个文章 URL 重试

## 实际可用数据量

| 接口 | 返回字段 | 可靠性 |
|---|---|---|
| `search` | title/desc/source/dateTime/url | ✅ 高 |
| `article_detail` | title/content/publish_time/user_info | ⚠️ 常失败 |

## 新旧版本差异

| 版本 | name | 差异 |
|---|---|---|
| v1.1.0 | wechat-official-content-search | 原有，基础搜索 |
| v1.2.2 | wechat-official-co | 新增 anti_hallucination 字段，详细失败元数据 |
| v1.2.4 | wechat-official-co | 同上，脚本略有更新 |

两个版本可并存，同时使用。