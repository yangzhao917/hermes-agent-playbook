# 配置指南

> Hermes Agent 完整配置方案 | 基于 v0.14.0

## 环境要求

- Python 3.11+
- Git
- 网络可达 GitHub（国内需代理）

## 安装步骤

```bash
# 克隆仓库
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 初始化配置
hermes setup
```

## config.yaml 关键配置项

```yaml
model:
  default: "MiniMax-M2.7"        # 默认模型
  provider: "minimax-cn"          # 提供商名称
  base_url: "https://api.minimaxi.com/v1"
  api_key: ""                     # 从环境变量或 .env 读取

agent:
  max_turns: 60                  # 最大对话轮次
  gateway_timeout: 1800          # 网关超时（秒）
  reasoning_effort: "medium"      # 推理强度

toolsets:
  - hermes-cli                    # 启用哪些工具集
```

## 更新 Hermes

```bash
cd ~/.hermes/hermes-agent
git pull upstream main
pip install -e .
hermes --version  # 确认版本
```

### v0.12.0 → v0.14.0 新功能

- agent-loop 函数调用减少 47%
- terminal 工具每次调用快 ~195ms
- xAI Web Search provider
- 浏览器 CDP 自动启动
- `hermes update` 语法校验 + 失败回滚
- Skill bundles（`/<bundle>` 一次加载多个技能）
- 元宝/飞书消息精确 ID 召回

## 飞书接入

- 飞书 App ID：`<YOUR_FEISHU_APP_ID>`
- 飞书用户 ID：`<YOUR_FEISHU_USER_ID>`
- 用户日历 ID：`<YOUR_FEISHU_CALENDAR_ID>`

## 微信接入

微信通过 WeChat Channel 接入，配置在 config.yaml 的对应 platform 区块。

## 常见安装错误

### 错误1：httpx SSL 错误

如果遇到 `httpx.ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING]`，可能是代理问题，尝试在代码中跳过系统代理：

```python
proxies={"http": None, "https": None},
trust_env=False
```

### 错误2：权限不足

```bash
pip install -e . --user
# 或使用 sudo
```
