# 睡眠数据同步到飞书日历

从可穿戴设备（手环/手表）截图提取睡眠数据，同步到飞书日历。

## 完整流程

### Step 1：提取图片数据

使用 `volc-vision` + 豆包模型分析图片：

```bash
ARK_API_KEY="ark-e8f26774-bc84-4ae0-861c-46d6fbc942c9-1bab7" \
  timeout 60 node /home/ubuntu/skills/volc-vision/index.js \
  /home/ubuntu/.hermes/image_cache/img_*.jpg \
  "提取这张睡眠数据截图中的所有信息：总睡眠时长、睡眠效率、各阶段分布（深度/轻度/安宁/苏醒）的分钟数、心率数据、呼吸数据、入睡时间、起床时间"
```

⚠️ **必须加 `ARK_API_KEY="..."` 内联传入**，不传会报 `Missing API key`。

WeChat 图片会缓存在 `/home/ubuntu/.hermes/image_cache/img_*.jpg`。

### Step 2：时间戳计算（Python，禁止手算）

```python
from datetime import datetime, timezone, timedelta
cst = timezone(timedelta(hours=8))

# 示例：2026-05-18 21:41 → 2026-05-19 01:28
start = datetime(2026, 5, 18, 21, 41, tzinfo=cst)
end   = datetime(2026, 5, 19, 1, 28, tzinfo=cst)

start_iso = start.isoformat()   # 2026-05-18T21:41:00+08:00
end_iso   = end.isoformat()     # 2026-05-19T01:28:00+08:00
```

### Step 3：写入飞书日历（lark-cli）

```bash
lark-cli calendar +create \
  --calendar-id "feishu.cn_J8U4kyolzluf358gBu6gNb@group.calendar.feishu.cn" \
  --summary "💤 睡眠" \
  --start "2026-05-18T21:41:00+08:00" \
  --end "2026-05-19T01:28:00+08:00" \
  --description "总睡眠时长：3小时47分钟
睡眠效率：47%

各阶段分布：
- 轻度睡眠：1小时37分钟（97分钟）
- 安宁睡眠（REM）：1小时4分钟（64分钟）
- 深度睡眠：1小时4分钟（64分钟）
- 苏醒次数：0次

心率数据：
- 平均心率：69 bpm
- 心率范围：59～86 bpm

呼吸数据：
- 平均呼吸率：13.1 次/分钟
- 呼吸率范围：11.5～21.5 次/分钟"
```

## 踩坑记录

### WeChat 图片上传后 AI 看不到

WeChat 图片需要通过 Hermes 的图片缓存机制访问，路径格式：`/home/ubuntu/.hermes/image_cache/img_*.jpg`。直接发送图片文件可能无法被 AI 视觉识别。如果 AI 看不到图，提示用户重新发送或检查图片是否成功上传到缓存。

### volc-vision 报 Missing API key

即使 ARK_API_KEY 已配置在环境中，调用时仍需内联传入：
```bash
ARK_API_KEY="ark-..." timeout 60 node .../index.js <path> "<prompt>"
```
不加内联会报 `Missing API key`。

### 睡眠时间段跨天（如 21:41 → 次日 01:28）

`--start` 用入睡当天日期，`--end` 用起床当天日期，时区统一 `+08:00`。
