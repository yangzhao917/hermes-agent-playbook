# MiniMax 模型配置经验沉淀

# MiniMax 模型配置经验沉淀

## 一、背景

Hermes Agent 主模型为 MiniMax\-M2\.7（MiniMax\-CN），备用模型为 DeepSeek V4 Flash。

## 二、⚠️ 重要：MiniMax 国际版 vs 中国版

<table><tbody>
<tr>
<td>

版本

</td>
<td>

Provider

</td>
<td>

API 地址

</td>
<td>

环境变量

</td>
</tr>
<tr>
<td>

**国际版**

</td>
<td>

`minimax`

</td>
<td>

`https://api\.minimax\.chat/v1`

</td>
<td>

`MINIMAX_API_KEY`

</td>
</tr>
<tr>
<td>

**中国版**

</td>
<td>

`minimax\-cn`

</td>
<td>

`https://api\.minimaxi\.com/v1`

</td>
<td>

`MINIMAX_CN_API_KEY`

</td>
</tr>
</tbody></table>

当前使用**中国版**（`minimax\-cn`）。

## 三、主模型：MiniMax\-M2\.7（中国版）

<table><tbody>
<tr>
<td>

项目

</td>
<td>

值

</td>
</tr>
<tr>
<td>

模型

</td>
<td>

MiniMax\-M2\.7

</td>
</tr>
<tr>
<td>

Provider

</td>
<td>

minimax\-cn

</td>
</tr>
<tr>
<td>

API 地址

</td>
<td>

`https://api\.minimaxi\.com/v1`

</td>
</tr>
<tr>
<td>

环境变量

</td>
<td>

`MINIMAX_CN_API_KEY`

</td>
</tr>
<tr>
<td>

API Key

</td>
<td>

``<MINIMAX_API_KEY>``

</td>
</tr>
<tr>
<td>

有效期

</td>
<td>

约一年（2027年5月左右到期）

</td>
</tr>
<tr>
<td>

来源

</td>
<td>

吴熠江提供

</td>
</tr>
</tbody></table>

**模型能力：**

- 文本生成（编程与 Agent SOTA）

- 视频生成（Hailuo 2\.3，1080p）

- 语音合成（40语言，实时响应）

- 音乐生成（文本转音乐）

- 语音克隆（5秒快速克隆）

- 图片生成

- 实时流式 API

- 高级推理（CoT 思维链，最长 128k tokens）

## 四、备用模型：DeepSeek V4 Flash

<table><tbody>
<tr>
<td>

项目

</td>
<td>

值

</td>
</tr>
<tr>
<td>

模型

</td>
<td>

deepseek\-v4\-flash

</td>
</tr>
<tr>
<td>

Provider

</td>
<td>

deepseek

</td>
</tr>
<tr>
<td>

API 地址

</td>
<td>

`https://api\.deepseek\.com`

</td>
</tr>
<tr>
<td>

API Key

</td>
<td>

``<DEEPSEEK_API_KEY>``

</td>
</tr>
</tbody></table>

**模型能力：**

- OpenAI/Anthropic 兼容 API

- 思考模式（Thinking Mode）

- 工具调用（Tool Calls）

- 上下文缓存（Context Caching）

- 多轮对话

## 五、配置生效方式

- **自动切换**：主模型（MiniMax）失败时自动切换到备用模型（DeepSeek）

- **手动生效**：修改配置后开启新 session 即可

## 六、验证命令

<table><tbody>
<tr>
<td>

操作

</td>
<td>

命令

</td>
</tr>
<tr>
<td>

查看当前模型

</td>
<td>

`hermes config show`

</td>
</tr>
<tr>
<td>

查看备用模型

</td>
<td>

`hermes fallback list`

</td>
</tr>
</tbody></table>

## 七、配置文件位置

`\~/\.hermes/config\.yaml`

关键配置项：

```XML
model:
  default: MiniMax-M2.7
  provider: minimax-cn
  base_url: https://api.minimaxi.com/v1

providers:
  deepseek:
    base_url: https://api.deepseek.com/v1
    model: deepseek-v4-flash
    api_key: <DEEPSEEK_API_KEY>

fallback_providers: deepseek
```

