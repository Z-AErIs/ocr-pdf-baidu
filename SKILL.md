---
name: ocr-pdf-baidu
description: Use when a PDF is scanned/image-based or text extraction fails, and you need to parse Chinese PDFs with Baidu document parsing or OCR before summarizing or researching them.
---

# 百度 OCR PDF 处理

将扫描版 PDF 转成可研究文本，再交给后续总结、分析和记录。

## 适用场景
- `pypdf` / `PyMuPDF` 抽不出正文
- 页面主要由图片组成
- 需要处理中文投资资料、研报、心得、表格扫描件

## 工作流
1. 先判断 PDF 类型：文本型、扫描件、或混合。
2. 文本型 PDF：直接抽取正文，不做 OCR。
3. 扫描件 PDF：优先调用百度文档解析 / 文档格式转换。
4. 文档解析失败、文件不适合或接口不可用时，回退到逐页图片 OCR。
5. 输出按页组织的 Markdown 和结构化 JSON。
6. 再把 Markdown 交给总结/研究流程。
7. 只把关键结论、分歧、可执行建议写入记忆。

## 处理原则
- 优先使用整份文档解析/格式转换；如果效果不稳，再退回按页 OCR。
- 保留页码、文件名、OCR 引擎、置信度和错误信息。
- 低置信度内容要显式标记，不要混入正文。
- 文件过大时先分割或分批处理，避免触发请求体/QPS 限制。
- 遇到 401/429/5xx，先重试一次并记录错误，再决定是否降级到页级 OCR。

## 输出约定
- `output.md`：按页输出的 Markdown，或文档解析生成的整篇 Markdown
- `output.json`：文件名、页数、引擎、置信度、错误摘要
- `ocr.log`：请求 ID、重试、失败原因

## 环境变量
- `BAIDU_OCR_API_KEY`
- `BAIDU_OCR_SECRET_KEY`
- 可选：`BAIDU_OCR_BASE_URL`
- 可选：`BAIDU_OCR_IMAGE_ENDPOINT`
- 可选：`BAIDU_OCR_LANGUAGE_TYPE`

## 脚本
- `scripts/detect_pdf_type.py`
- `scripts/ocr_pdf.py`
- `scripts/export_markdown.py`

## 参考
- `references/baidu-ocr-notes.md`
- `references/baidu-document-parse.md`
- `references/baidu-api-example.md`

## 不要使用这个技能的情况
- PDF 本身可直接抽取文本
- 只是网页、图片或普通文档，不需要 OCR
- 只想快速口头摘要，不需要保存中间文本
