# Feishu 文档导出与知识库建设工作流

## 场景

将飞书文档导出为 Markdown，整理成分类知识库（如 playbook、经验手册）并同步到 GitHub。

## 完整工作流

### 1. 搜索飞书文档

```bash
lark-cli drive +search --query "关键词" --doc-types "doc,docx" --format "pretty"
```

### 2. 导出文档（注意路径约束）

```bash
# ⚠️ --output-dir 必须是相对路径，不能是绝对路径
cd /目标目录
lark-cli drive +export \
  --token "<doc_token>" \
  --doc-type "docx" \
  --file-extension "markdown" \
  --output-dir "./feishu-docs" \
  --overwrite
```

> ⚠️ **重要**：`--output-dir` 必须是**相对路径**，且必须先 `cd` 到目标目录。绝对路径会报错：`unsafe output path`

### 3. 整理分类

导出后按场景/主题重新组织目录结构，例如：
```
playbook/
├── 飞书集成/
├── 微信使用/
├── 定时任务/
├── 用户规约/
├── 配置指南/
└── 技能管理/
```

### 4. 初始化 Git 仓库（首次）

```bash
mkdir playbook && cd playbook
git init
git config user.email "your-email@xxx"
git config user.name "your-username"
git add -A && git commit -m "Initial commit"
```

### 5. 添加 GitHub remote 并推送

```bash
# 添加 remote（含 token）
git remote add origin "https://<TOKEN>@github.com/<username>/<repo>.git"

# 首次推送
git push origin master:main --force
```

### 6. 后续更新流程

```bash
git add -A
git commit -m "更新说明"
git push origin master:main --force
```

> ⚠️ **用户确认原则**：批量更新内容（多个文件）推送前应告知用户，确认后再 push，避免覆盖用户已修改的内容

## 关键约束汇总

| 约束 | 说明 |
|------|------|
| `--output-dir` 必须是相对路径 | 绝对路径报错 `unsafe output path` |
| 先 `cd` 到目标目录再执行 export | lark-cli 要求当前目录在输出路径的父路径 |
| Git remote URL 含 token | 格式：`https://<TOKEN>@github.com/...` |
| Force push 前确认 | 避免覆盖用户已在 GitHub 网页端修改的内容 |
