# 模型 Provider 配置

## 定位

AgentOS 依赖模型 provider 提供理解、总结、规划和工具调用能力。模型配置的目标不是绑定单一厂商，而是让运行时具备主模型、备用模型和故障切换能力。

当前经验沉淀主要覆盖 MiniMax 中国版和 DeepSeek 备用模型。文档只保留通用配置方法，不保存真实 API key、账号来源、有效期或个人授权信息。

## Provider 区分

MiniMax 国际版和中国版的 provider、base URL 和环境变量不同，配置时必须明确区分。

| 版本 | Provider | Base URL | 环境变量 |
| --- | --- | --- | --- |
| MiniMax 国际版 | `minimax` | `https://api.minimax.chat/v1` | `MINIMAX_API_KEY` |
| MiniMax 中国版 | `minimax-cn` | `https://api.minimaxi.com/v1` | `MINIMAX_CN_API_KEY` |
| DeepSeek | `deepseek` | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` |

## MiniMax 中国版协议模式

MiniMax 中国版当前应走 OpenAI-compatible Chat Completions 协议。Hermes 配置里必须明确使用：

```yaml
model:
  default: MiniMax-M2.7
  provider: minimax-cn
  base_url: https://api.minimaxi.com/v1
  api_mode: chat_completions
```

不要把 `minimax-cn` 配成 `api_mode: anthropic_messages`。该模式会请求 `/v1/messages`，当前会返回 `HTTP 404: 404 page not found`。正确路径是 `/v1/chat/completions`。

验证协议是否正确：

```bash
curl -sS https://api.minimaxi.com/v1/models >/dev/null
# Hermes 主模型验证：
hermes chat -q "只回复：OK" --quiet
```

## 推荐运行策略

AgentOS 推荐采用主备模型策略：

```text
主模型：负责日常对话、复盘、总结和工具调用
备用模型：主模型失败、限流或认证异常时兜底
```

模型失败时，输出里要区分：

- 事实：接口是否返回 401、429、5xx 或超时。
- 判断：是否需要切换备用模型。
- 不确定：是否由账号、网络、限流或 provider 配置导致。
- 建议：下一步验证命令或回滚动作。

## 配置示例

示例仅展示结构，不包含真实 key。

```yaml
model:
  default: MiniMax-M2.7
  provider: minimax-cn
  base_url: https://api.minimaxi.com/v1
  api_mode: chat_completions

providers:
  minimax-cn:
    base_url: https://api.minimaxi.com/v1
    api_key_env: MINIMAX_CN_API_KEY

  deepseek:
    base_url: https://api.deepseek.com/v1
    model: deepseek-v4-flash
    api_key_env: DEEPSEEK_API_KEY

fallback_providers:
  - deepseek
```

真实配置应放在 Hermes 运行态配置或私有环境变量中，不进入 AgentOS 仓库。

## 验证

查看当前配置：

```bash
hermes config show
```

查看 fallback 配置：

```bash
hermes fallback list
```

验证环境变量是否存在：

```bash
printenv MINIMAX_CN_API_KEY >/dev/null && echo ok || echo missing
printenv DEEPSEEK_API_KEY >/dev/null && echo ok || echo missing
```

验证网络是否可达：

```bash
curl -sS https://api.minimaxi.com/v1 >/dev/null
curl -sS https://api.deepseek.com/v1 >/dev/null
```

## 常见问题

### Provider 名称和 base URL 不匹配

现象：模型请求认证失败、404 或 provider 初始化失败。

处理：确认 provider、base URL、环境变量使用同一版本，例如中国版 MiniMax 使用 `minimax-cn`、`https://api.minimaxi.com/v1` 和 `MINIMAX_CN_API_KEY`。

### API key 缺失或过期

现象：401、invalid token、authentication failed。

处理：在私有环境中更新 key；不要把 key 写入仓库、日志、飞书文档或微信消息。

### 网络可达但模型不可用

现象：curl 可访问 provider 域名，但 Hermes 调用失败。

处理：分别检查 Hermes provider 配置、环境变量、模型名称和 fallback 策略。

### 主模型失败后没有 fallback

现象：主模型 401、429 或超时后任务直接失败。

处理：确认 fallback provider 已配置，并在复盘中记录模型故障和实际兜底结果。

## 安全规则

- 不提交 API key、token、账号来源、有效期和个人授权信息。
- 不在公开文档里写真实 provider 账号信息。
- 模型故障复盘可以记录错误类型，但不记录完整请求头或密钥片段。
- 需要长期保留的真实配置放在私有运维目录，不进入 Git。
