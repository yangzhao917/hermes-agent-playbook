# 图片文字识别（OCR）备选方案

## 背景

MiniMax-M2 vision API（`vision_analyze` tool）偶发报错：
```
unknown variant `image_url`, expected `text` at line 1 ...
```
此时 API 拒绝处理，需换用 OCR。

## 适用场景

- `vision_analyze` 报 400 错，且确认图片格式正常（`file` 命令验证）
- 图片含中文车票/凭证/截图等非 logo 类文字

## 方案：tesseract OCR

```bash
# 安装（若未装）
sudo apt-get install tesseract-ocr

# 识别中文+英文，限制输出行数
tesseract /path/to/image.jpg stdout -l chi_sim+eng 2>/dev/null | head -80
```

| 参数 | 含义 |
|------|------|
| `chi_sim+eng` | 中文简体 + 英文 |
| `stdout` | 输出至管道 |
| `2>/dev/null` | 压制 tesseract 诊断信息 |
| `head -N` | 按需截断，避免过量输出 |

## 已知限制

- `vision_analyze` 在本地文件路径格式（`/absolute/path`）下仍报 `unknown variant image_url`，说明工具本身对该格式有路径解析问题
- 将图片通过 HTTP server 暴露（`python3 -m http.server`）也失败，API 不接受 `localhost` URL
- ffmpeg 缩放图片后再识别可行（减小体积），但 tesseract 本身就能处理 149K JPEG，无需预处理

## 图片预处理（如需）

```bash
# ffmpeg 缩放（供 vision_analyze 重试用）
ffmpeg -i input.jpg -vf "scale=414:896" -quality 85 /tmp/vision_resize.jpg -y

# ImageMagick（若装过）
convert input.jpg -resize 800 /tmp/vision_resize.jpg
```

## 质量对比

| 工具 | 场景 | 效果 |
|------|------|------|
| `vision_analyze` | 普通截图/照片 | ✅ 最佳 |
| `tesseract -l chi_sim+eng` | 车票/行程单/表格 | ✅ 可用（中文字符） |
| ffmpeg 预处理 | 太大图片（>2MB） | ⚠️ 仅辅助 vision 重试 |

## 总结判断流程

```
vision_analyze 失败?
  → 验证图片正常: file xxx.jpg
  → 试 tesseract（快，成本低）
  → 若 tesseract 不够用，尝试 ffmpeg 缩放后再 vision_analyze
```