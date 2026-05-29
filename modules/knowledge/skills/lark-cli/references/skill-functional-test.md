# lark-cli 功能验证记录 (2026-05-20)

验证时间：2026-05-20
验证版本：lark-cli v1.0.33

---

## 任务模块 ✅ 全部通过

### 1. tasks list 过滤查询
| 用法 | 结果 |
|------|------|
| `completed: false` | ✅ 返回未完成任务，status=todo |
| `completed: true` | ✅ 返回已完成任务，status=done |
| 不填 completed | 返回混合列表（不过滤） |

```bash
lark-cli task tasks list --params '{"completed": false, "page_size": 40}' --format json
lark-cli task tasks list --params '{"completed": true, "page_size": 40}' --format json
```

### 2. +create 创建任务
| 测试项 | 结果 |
|--------|------|
| 创建带截止日期+负责人 | ✅ 成功，guid 正确返回 |
| --due 接受 ISO 8601 | ✅ |
| --assignee 必须（user open_id） | ✅ |

### 3. +complete 标记完成
| 判断条件 | 说明 |
|----------|------|
| 成功响应 | `{"ok": true, "data": {"guid": "..."}}` |
| 失败响应 | `{"ok": false, ...}` |

### 4. +reopen 重新打开
| 测试项 | 结果 |
|--------|------|
| 已完成 → 重新打开 | ✅ status 恢复为 todo |
| 响应格式 | 与 +complete 相同 |

### 5. 批量操作
| 方式 | 结果 |
|------|------|
| 串行循环 `--task-id` | ✅ 逐个成功 |
| 并行 xargs | ❌ 输出交织，无法判断成败 |
| 循环中 `+complete "$guid"`（位置参数） | ❌ 只有第一个被执行 |
| 循环中 `+complete --task-id "$guid"` | ✅ 全部成功 |

---

## 日历模块 ✅ 全部通过

### 1. +agenda 查看日程
| 测试项 | 结果 |
|--------|------|
| --start/--end ISO 8601 | ✅ |
| --calendar-id | ✅ 支持指定日历 |
| 无日程时返回 | `{"data": []}`（空数组，非报错） |

### 2. +freebusy 查询忙闲
| 测试项 | 结果 |
|--------|------|
| --user-id 指定用户 | ✅ |
| --start/--end ISO 8601 | ✅ |
| 自身日历查询 | 返回 `{"data": null}`（正常，非报错） |

### 3. +create 创建日程
| 测试项 | 结果 |
|--------|------|
| 创建成功 | ✅ `event_id` 在 `data` 中返回 |
| start/end ISO 8601 | ✅ |
| summary 标题 | ✅ |

### 4. events patch 更新日程
| 测试项 | 结果 |
|--------|------|
| 修改 summary | ✅ `code: 0` |
| 修改 start/end 时间 | ✅ |
| --params 传路径参数 | ✅ |
| --data 传 body JSON | ✅ |
| --data @file 相对路径 | ✅（绝对路径报错） |

### 5. events delete 删除日程
| 测试项 | 结果 |
|--------|------|
| 删除成功 | ✅ `code: 0` |
| 删除已删除日程 | ✅ 返回 `code: 193003, message: event is deleted` |

---

## 已知行为（文档已有）

| 行为 | 说明 |
|------|------|
| `+agenda` 无日程 | 返回 `{"data": []}`（空数组），非报错 |
| `+freebusy` 自身日历 | 返回 `{"data": null}`，非报错 |
| `events patch` 只改 summary | 只传 summary 字段即可，不需要全部字段 |
| `tasks patch` status 不可更新 | 必须用 `+complete --task-id` |

---

## 验证结论

所有核心 CRUD 操作均通过验证，skill 文档中的用法正确。
