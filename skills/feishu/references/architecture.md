# 飞书技能栈：层级关系与职责分工

## 三层架构

```
productivity/feishu  (定制高阶技能，888行)
  └── 定义本用户的工作流规则、约束、铁律
  └── 不直接调 API，编排下层技能完成任务

feishu-task          (Python 封装层，96行)
  └── 封装飞书任务的 CRUD 操作
  └── 6个脚本：列表/创建/完成/批量完成/搜索/统计

lark-cli             (官方 CLI 技能，739行)
  └── larksuite/cli 官方工具
  └── 200+ 命令覆盖日历/文档/云空间/任务等
  └── token 自己管，不依赖手动同步
```

## 职责边界

| 技能 | 职责 | 调用方 |
|------|------|--------|
| `lark-cli` | 底层 API 调用，直调飞书 HTTP | `feishu-task` / `daily-review` |
| `feishu-task` | 任务维度的快捷封装，可编程调用 | `productivity/feishu` / 脚本 |
| `productivity/feishu` | 工作流规则、高层编排、平台约束 | Agent 直接使用 |

## 不要做的事

- `~/.hermes/skills/feishu/` 是空目录（已删除），不要重建
- `productivity/feishu` 是**定制技能**，不是官方 skill
- 遇到飞书操作问题，先查 `lark-cli` SKILL.md，再查本技能

## 关联技能

- `lark-cli`：必须加载的底层依赖
- `feishu-task`：任务操作的 Python 封装层
- `daily-review`：依赖本技能进行飞书文档写入
