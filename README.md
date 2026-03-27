# OCR PDF Baidu / 百度 OCR PDF 处理

OpenClaw skill for converting scanned or text-based Chinese PDFs into Markdown using Baidu OCR.

## 中文简介

这是一个用于处理中文 PDF 的 OpenClaw skill，适合将**扫描版**或**文本型** PDF 转成可研究的 Markdown，并为后续摘要、研究和归档流程提供统一入口。

它支持：

- 自动识别 PDF 是文本型、扫描型还是混合型
- 文本型 PDF 直接抽取正文
- 扫描型 PDF 优先使用百度文档解析
- 文档解析失败时回退到逐页 OCR
- 输出 Markdown 和 JSON，方便后续研究工作流使用

## 功能

- 检测 PDF 是否为文本型、扫描型或混合型
- 直接提取文本型 PDF 的正文
- 对扫描型 PDF 优先使用百度文档解析 / 文档格式转换
- 必要时回退到逐页图片 OCR
- 导出 Markdown 和 JSON，供后续研究、摘要和归档使用

## 仓库结构

```text
ocr-pdf-baidu/
├── SKILL.md
├── README.md
├── LICENSE
├── .gitignore
├── dist/
│   └── ocr-pdf-baidu.skill
├── references/
│   ├── baidu-api-example.md
│   ├── baidu-document-parse.md
│   └── baidu-ocr-notes.md
└── scripts/
    ├── detect_pdf_type.py
    ├── export_markdown.py
    └── ocr_pdf.py
```

## 快速开始

```bash
cd ocr-pdf-baidu
export BAIDU_OCR_API_KEY="..."
export BAIDU_OCR_SECRET_KEY="..."
python3 scripts/ocr_pdf.py ./sample.pdf --mode auto --out-md ./out.md --out-json ./out.json
```

## 推荐使用流程

1. 先用 `scripts/detect_pdf_type.py` 检测 PDF 类型
2. 再用 `scripts/ocr_pdf.py` 的 `auto` 模式处理
3. 检查生成的 Markdown
4. 将 Markdown 交给你的摘要 / 研究工作流
5. 需要分发时，使用 `dist/ocr-pdf-baidu.skill` 打包成果

## 注意事项

- 这个仓库是为 OpenClaw skills 设计的
- 百度 OCR 的 API Key / Secret Key 不要提交到仓库，请放在环境变量或密钥管理工具中
- 对于较大的 PDF，建议优先使用文档解析；页级 OCR 只作为兜底

## English Overview

OpenClaw skill for converting scanned or text-based Chinese PDFs into Markdown using Baidu OCR.

## What it does

- Detects whether a PDF is text-based, scanned, or mixed.
- Extracts text directly from text-based PDFs.
- Prefers Baidu document parsing for scanned PDFs.
- Falls back to page-by-page OCR when needed.
- Exports Markdown and JSON outputs for downstream research workflows.

## Quick start

```bash
cd ocr-pdf-baidu
export BAIDU_OCR_API_KEY="..."
export BAIDU_OCR_SECRET_KEY="..."
python3 scripts/ocr_pdf.py ./sample.pdf --mode auto --out-md ./out.md --out-json ./out.json
```

## Recommended workflow

1. Run `scripts/detect_pdf_type.py` on a sample PDF.
2. Use `scripts/ocr_pdf.py` in `auto` mode.
3. Review the generated Markdown.
4. Feed the Markdown into your research/summary workflow.
5. Package with the `.skill` artifact in `dist/` for OpenClaw distribution.

## Notes

- This repository is designed to be used with OpenClaw skills.
- The Baidu OCR keys are never committed; set them in your shell or secret manager.
- For large PDFs, prefer document parsing first and page OCR as fallback.
