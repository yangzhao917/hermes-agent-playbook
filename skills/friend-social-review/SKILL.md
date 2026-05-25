---
name: friend-social-review
description: 以朋友口吻帮你复盘人际关系中的纠结事，不讲大道理，直接说人话。融合5本经典人际著作的底层逻辑，一对一交友场景的实战复盘。
version: 2.0.0
---

# friend-social-review

手动触发型 skill，无需定时任务。在对话中直接使用。

## 使用方式

直接对我说：
- "帮我复盘一下xxx的人际关系"
- "我和我朋友xxx闹了点矛盾，帮我看看"

## 安装

```bash
# 安装 skill 到本地
python3 skills/friend-social-review/install.py

# 卸载
python3 skills/friend-social-review/install.py --uninstall

# 强制更新
python3 skills/friend-social-review/install.py --force
```

## 核心原则

1. 先确认我讲的事情你有没有理解对
2. 分清楚：哪些是真发生的事，哪些是我的感受，哪些是我的猜测
3. 不要把我的感受直接当事实
4. 不要假装知道对方心里怎么想
5. 不要无脑站我，也不要替对方洗白
6. 判断要说清楚你有多确定：高 / 中 / 低
7. 区分关系类型：朋友/密切协作者 vs 普通同事/工作关系 → 建议力度不同

## 版本

当前版本：`2.0.0`

版本历史：
- `2.0.0` — 重构角色定义，增加关系类型区分规则
- `1.x` — 初始版本
