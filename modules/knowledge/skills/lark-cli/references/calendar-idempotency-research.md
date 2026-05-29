# 飞书日历 API 幂等性 / 批量 / 性能 研究（2026-05-22 官方文档确认）

## 幂等性

**创建日程支持 `idempotency_key`（查询参数，非请求体）：**
- 位置：HTTP URL `?idempotency_key=xxx`
- 范围：应用维度 + 日历维度，唯一
- 长度：32 ~ 128 字符
- 效果：相同 key 的重复请求返回已创建的日程，不重复创建
- 建议生成方式：
  ```python
  import hashlib
  def make_idempotency_key(calendar_id: str, summary: str, start_ts: int) -> str:
      raw = f"{calendar_id}:{summary}:{start_ts}"
      return hashlib.md5(raw.encode()).hexdigest()[:32]
  ```

## 批量操作

| 操作 | 官方支持 |
|------|---------|
| 批量创建 | ❌ 无 batch API，只能循环单条 + idempotency_key 防重 |
| 批量删除 | ❌ 无 batch API，只能循环单条 |
| 批量更新 | ❌ 无 batch API |
| 批量查（分页） | ✅ list API 支持 `page_token` 分页（50-1000条/页），`sync_token` 增量同步 |

## 性能 / 限流

- 频率限制：**1000次/分钟、50次/秒**（日历 CRUD 通用）
- 限流响应：HTTP 429，`x-ogw-ratelimit-reset` 头指定恢复秒数
- 处理方式：捕获 429，按 `x-ogw-ratelimit-reset` 等待后重试，指数退避
- 批量操作必须串行，禁止并行（输出交织无法判断成功/失败）

## list_events 时间范围参数

- `start_time` + `end_time`：Unix 秒级时间戳，与 page_token/sync_token 互斥
- `anchor_time`：直拉某时间点之后，避免全量拉取
- `page_size`：50-1000，默认 500

## create_event 关键字段

- `idempotency_key`：查询参数（?idempotency_key=），不是请求体
- `start_time.timestamp`：秒级 Unix 时间戳（字符串），不是毫秒
- `end_time.timestamp`：秒级 Unix 时间戳（字符串）
- `timezone`：默认 Asia/Shanghai
- `vchat.vc_type`：需传 `no_meeting` 表示无视频会议（否则自动创建）

## API 文档原始链接

- 创建日程：https://open.feishu.cn/document/server-docs/calendar-v4/calendar-event/create
- 获取日程列表：https://open.feishu.cn/document/server-docs/calendar-v4/calendar-event/list
- 删除日程：https://open.feishu.cn/document/server-docs/calendar-v4/calendar-event/delete
- 频控策略：https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN
