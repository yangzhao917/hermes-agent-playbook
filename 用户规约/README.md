# 用户规约

> 踩坑记录与硬规矩（已移出内容见各 skill 文档）

## 时间计算类

| 规约 | 说明 | 来源 |
|------|------|------|
| Python 计算时间戳 | 禁止手算或硬编码，所有日期计算走 Python datetime | 硬规矩 |
| 日历 timestamp 用秒级 Unix | `start_time.timestamp` / `end_time.timestamp` 是秒级 | lark-cli skill |
| 任务 due 用毫秒级 | `due.timestamp` 是毫秒级（×1000） | lark-cli skill |

---

> **已移出：**
> - 交互偏好类（微信只给结论、先执行再汇报、禁止家庭角色用语）→ user profile memory
> - 飞书操作类 → 各飞书 skill 文档
