# 微信公众号正文读取限制记录

## 问题描述

当前环境下，`article_detail` action 持续返回：

```json
{"code": 301, "message": "COLLECT FAILED, SEND REQUEST AGAIN"}
```

多次重试结果一致（试过 5+ 次），确认不是临时抖动。

## 根因

微信公众号有 CAPTCHA 验证拦截机制，Just One API 的采集请求被识别并拦截。

症状表现：
- 搜索（`search` action）：✅ 正常工作
- 公众号发文列表（`user_posts` action）：✅ 正常工作
- 文章正文（`article_detail` action）：❌ 结构性失败
- 文章评论（`article_comments` action）：未测试（依赖 article_detail）

## 临时替代方案

1. **搜索摘要替代法**：用 `search` action 的 `title` + `desc` 字段作为主要信息来源
   - `desc` 字段含文章摘要/描述，通常有 100-200 字，足以支撑信息提取
   - `title` 字段含文章标题（高亮关键词）

2. **直接让用户提供**：要求用户贴原文正文或截图

## 验证时间

2026-05-27