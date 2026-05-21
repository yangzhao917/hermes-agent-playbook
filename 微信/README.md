# 微信

> 微信消息机制、意图识别与分发规则

## 消息队列机制

微信消息进来后：

1. **Agent 在 busy** → 新消息排队，等当前 turn 结束后自动处理
2. **Agent 在 idle** → 新消息立即响应

### 连续发消息

直接发，不用等，队列会自动排，依次执行。

### 打断当前任务

- `/stop` + 新任务 → 强制打断 + 执行新任务
- `/reset` → 清空对话历史重新开始

## 消息分发规则

**微信只发简版（一屏），飞书存全文。**

- 完成事项 + 明日待办 + 待跟进
- 具体数据和分析结论放飞书

## 相关 Issue

- [Context-aware task switching for WeChat/messaging platforms](https://github.com/NousResearch/hermes-agent/issues/29869)（Feature Request，尚未实现）
