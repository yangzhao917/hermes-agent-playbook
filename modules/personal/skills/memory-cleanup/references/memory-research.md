# 记忆清理研究参考

## 官方设计（Hermes 文档）

来源：https://hermes-agent.nousresearch.com/docs/user-guide/features/memory

### 核心原则

- **容量满了再管**：系统在接近 80% 容量时报错，届时 consolidation
- **精确重复系统自动拦截**：无需 skill 处理
- **不设 TTL/过期时间**：持久事实永不过期
- **按需触发**：用户说"清理记忆"才跑，不是定时任务

### 容量限制

| 存储 | 限制 | 建议 |
|------|------|------|
| MEMORY.md | 2,200 chars | 8-15 条目 |
| USER.md | 1,375 chars | 5-10 条目 |

## v1 规则论证

| 规则 | 问题 | 结论 |
|------|------|------|
| 版本号引用删除 | 工具路径中的版本号是持久事实，不是临时状态 | 删除依据不成立 |
| 7天一次性事件过期 | 飞书 token 有效期是7天，但路径"有效期"不是7天（变了才过期，没变就没过期） | 时间阈值无数据支撑 |
| 30天阈值 | 无任何证据支持30天优于其他值 | 任意设定 |

## 正确方法

**触发**：用户说"清理记忆" → skill 执行

**只删**：
- 精确重复（保险层）
- 临时代码快照（失效时报错提示）
- 用户明确推翻的偏好

**不删**：
- 持久环境事实
- 用户偏好
- auth/token 配置

## 参考论文

- Lilian Weng, "LLM-powered Autonomous Agents", 2023 — 记忆分类（STM/LTM）
- Park et al., "Generative Agents", 2023 — importance × recency × relevance 检索评分
