# 小红书账号解析：red_id（展示号）vs userId（内部ID）

## 核心区别

| 字段 | 示例 | 用途 | API可用性 |
|------|------|------|----------|
| 小红书号（red_id / display number） | `94348811612`, `1323051823` | 用户分享时显示的ID | **不能**直接用于API的 `userId` 参数 |
| 内部 userId | `6252583b00000000210299ba` | 平台内部唯一标识 | **可以**用于API的 `userId` 参数 |

## 为什么不能混用

API 的 `userId` 参数需要的是**内部 userId**（24位十六进制字符串），而不是用户在个人页面看到的"小红书号"。

直接拿 red_id 调用 API 会报错：
```
code: 400, message: "param userId not right"
```

## 如何获取正确的 userId

### 方法1：通过搜索 API 反查（最可靠）

```bash
# 搜索用户名，获取其 userId
curl -s --noproxy '*' -G \
  --data-urlencode "token=$JUSTONEAPI_TOKEN" \
  --data-urlencode "keyword=目标账号昵称" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=5" \
  "https://api.justoneapi.com/api/xiaohongshu/search-user/v2"
```

返回结果中的 `id` 字段即为内部 userId。

### 方法2：通过笔记数据间接获取

```bash
# 搜索某账号发布的笔记，从笔记数据中提取 userId
curl -s --noproxy '*' -G \
  --data-urlencode "token=$JUSTONEAPI_TOKEN" \
  --data-urlencode "keyword=关键词" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=20" \
  "https://api.justoneapi.com/api/xiaohongshu/search-note/v3"
```

笔记数据结构中：
```json
{
  "note": {
    "user": {
      "userid": "6252583b00000000210299ba",   // <-- 内部 userId
      "red_id": "1323051823",                 // <-- 展示号（red_id）
      "nickname": "十堰黑客松"
    }
  }
}
```

## 短链接（xhslink.com）已失效

- `xhslink.com/m/xxx` 短链接会过期或被回收，本session中 `https://xhslink.com/m/410Ui7zryeL` 返回 `HTTP/2 404`
- **不要依赖短链接**，直接让用户提供小红书主页 URL `https://www.xiaohongshu.com/user/profile/xxx`（这里的 xxx 也是 red_id）

## get-user-note-list 返回 301 的处理

`/api/xiaohongshu/get-user-note-list/v4` 对部分账号返回 `code=301 FAILED, RETRY`，表示该接口对目标账号采集失败（非参数问题），换账号/重试无法解决，是接口侧限制。

## 踩坑记录（本session实测）

| 错误做法 | 正确做法 |
|----------|----------|
| 用 red_id `94348811612` 直接作为 userId 调用 get-user/v3 | 先通过 search-user/v2 用昵称找到内部 userId，再用 userId 调用 |
| 依赖 xhslink.com 短链接 | 改让用户提供完整小红书主页 URL |
| 以为 94348811612 和 1323051823 是同一个账号的不同格式 | 两者都是 red_id，但对应不同账号，需通过搜索确认 |