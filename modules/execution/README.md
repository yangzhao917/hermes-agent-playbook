# Execution Module

执行模块把 AgentOS 的判断落到具体日程和任务动作。

## Skills

- `feishu-calendar`
- `feishu-task`

## 边界

当动作会创建、删除或修改外部状态，并且可能带来噪音或不可逆影响时，必须先确认。
