# wechat-official-justone-skill v1.2.4

用于通过 Just One API 获取微信公众号公开内容的 Hermes/ChatGPT Skill。

## 当前状态

- ✅ 公众号搜索正常
- ⚠️ 文章正文读取存在限流 / `COLLECT FAILED` 风险
- ✅ 已内置限速、缓存、URL 去重、降级和防幻读规则

## 文件结构

```text
wechat-official-justone-skill-v1.2.4/
├── SKILL.md
├── README.md
├── requirements.txt
└── scripts/
    └── wechat_official_client.py
```

## 环境变量

除 Token 外，其他运行参数已内置默认值；不配置也会使用下面的默认值。

```bash
export JUSTONE_API_TOKEN="你的 token"
# 可选：本机/私有部署兜底，JUSTONE_API_TOKEN 未配置时读取；不要提交真实 token

# 默认国际地址；国内服务器可改为官方文档中的大陆地址
export JUSTONE_API_BASE_URL="https://api.justoneapi.com"
# export JUSTONE_API_BASE_URL="http://47.117.133.51:30015"

# 正文读取建议超时至少 60 秒，本脚本默认 75 秒
export JUSTONE_TIMEOUT="75"

# COLLECT FAILED 不建议强重试，默认最多 1 次网络/服务级重试
export JUSTONE_MAX_RETRIES="1"

# article_detail 限速：两次正文读取之间至少间隔 8 秒
export JUSTONE_DETAIL_MIN_INTERVAL_SECONDS="8"

# 成功缓存：正文 7 天，搜索 6 小时
export JUSTONE_DETAIL_CACHE_TTL_SECONDS="604800"
export JUSTONE_SEARCH_CACHE_TTL_SECONDS="21600"
export JUSTONE_CACHE_DIR=".cache/justone_wechat"
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 常用命令

```bash
# 搜索公众号文章，最新排序
python scripts/wechat_official_client.py search \
  --keyword "黑客松" \
  --offset 0 \
  --search-type _2 \
  --sort-type _2

# 搜索公众号账号
python scripts/wechat_official_client.py search \
  --keyword "AI Agent" \
  --search-type _1

# 获取公众号发文
python scripts/wechat_official_client.py user_posts \
  --wxid "rmrbwx"

# 获取文章详情：会自动 URL 去重、限速、成功缓存
python scripts/wechat_official_client.py article_detail \
  --article-url "https://mp.weixin.qq.com/s/xxxx"

# 获取文章互动指标
python scripts/wechat_official_client.py article_feedback \
  --article-url "https://mp.weixin.qq.com/s/xxxx"

# 获取文章评论
python scripts/wechat_official_client.py article_comments \
  --article-url "https://mp.weixin.qq.com/s/xxxx"
```

## 解决正文读取限流的策略

不能通过高并发、代理池、频繁重试来绕过限流。本版本采用更稳的工程策略：

1. 搜索优先，正文按需读取。
2. `article_detail` 默认串行调用。
3. 两次正文读取默认间隔 8 秒。
4. 成功读取的正文缓存 7 天，避免重复采集。
5. 自动规范化微信文章 URL，减少重复请求。
6. `COLLECT FAILED` / `code=301` 不连续强重试，直接降级。
7. 正文失败时进入候选线索模式，防止模型幻读。

## 正文读取失败策略

如果 `article_detail` 返回 `COLLECT FAILED`、`code != 0`、`data` 为空或没有正文内容字段：

- 不生成完整文章摘要
- 不补全报名链接、赛程、地点、奖项、主办方
- 只能基于搜索接口返回的标题、摘要、发布时间、公众号名称、文章链接整理线索
- 缺失字段标注为“未获取到”
- 输出“候选活动线索”，不能写成“已确认活动详情”

## 本地检查

```bash
python -m py_compile scripts/wechat_official_client.py
python scripts/wechat_official_client.py --help
```

## 真实接口测试建议

```bash
# 1. 先测搜索
python scripts/wechat_official_client.py search --keyword "AI Agent" --search-type _2 --sort-type _2

# 2. 再挑 1 条文章测正文，不要批量测
python scripts/wechat_official_client.py article_detail --article-url "搜索结果中的文章链接"
```

## 默认环境变量

脚本已经内置非敏感默认值：

- `JUSTONE_API_BASE_URL=https://api.justoneapi.com`
- `JUSTONE_TIMEOUT=75`
- `JUSTONE_MAX_RETRIES=1`
- `JUSTONE_DETAIL_MIN_INTERVAL_SECONDS=8`
- `JUSTONE_DETAIL_CACHE_TTL_SECONDS=604800`
- `JUSTONE_SEARCH_CACHE_TTL_SECONDS=21600`
- `JUSTONE_CACHE_DIR=.cache/justone_wechat`

Token 不能使用公共默认值。脚本只读取 `JUSTONE_API_TOKEN`；没有配置时会直接报错，防止模型在无数据情况下继续幻读。

可复制 `.env.example`：

```bash
cp .env.example .env
# 然后把 your_token_here 改成真实 token
```
