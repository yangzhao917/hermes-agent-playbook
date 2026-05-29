# ima-skill 安装与验证记录

## 安装路径

skill 放在 `~/.hermes/skills/ima-skill/`，不在 `productivity/` 子目录下。

```
~/.hermes/skills/ima-skill/
├── SKILL.md
├── ima_api.cjs
├── meta.json
├── knowledge-base/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
└── notes/
    ├── SKILL.md
    └── references/
```

## 凭证配置

```bash
mkdir -p ~/.config/ima
echo "<ClientID>" > ~/.config/ima/client_id
echo "<APIKey>" > ~/.config/ima/api_key
```

`ima_api.cjs` 读取顺序：环境变量 `IMA_OPENAPI_CLIENTID` / `IMA_OPENAPI_APIKEY` → `~/.config/ima/client_id` / `api_key`。

## 验证成功的 API

```bash
SKILL_DIR="$HOME/.hermes/skills/ima-skill"
OPTS='{"clientId":"<ID>","apiKey":"<Key>"}'
node "$SKILL_DIR/ima_api.cjs" "openapi/check_skill_update" '{"version":"1.1.7"}' "$OPTS"
# → code:0，说明凭证正常

node "$SKILL_DIR/ima_api.cjs" "openapi/note/v1/list_notebook" '{"cursor":"0","limit":3}' "$OPTS"
# → code:0，返回笔记列表
```

## 验证失败的 API

- `openapi/v2/subscribe/list` → HTTP 404，接口路径不存在，不要使用

## 更新检查

`ima_api.cjs` 内置每天首次自动检查更新，可手动强制：
```bash
export IMA_FORCE_UPDATE_CHECK=1
```