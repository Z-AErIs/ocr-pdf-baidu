# OCR PDF Baidu

> OpenClaw skill for converting scanned or text-based Chinese PDFs into Markdown using Baidu OCR.
>
> 将扫描版或文本型中文 PDF 转成 Markdown，适合 OpenClaw 投研 / 资料整理工作流。

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://github.com/Z-AErIs/ocr-pdf-baidu)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

`ocr-pdf-baidu` is an OpenClaw skill that turns PDFs into research-friendly Markdown.
It is designed for Chinese investment materials such as reports, notes, announcements, and screenshots.

It follows a simple pipeline:

1. Detect whether the PDF is text-based, scanned, or mixed.
2. Extract text directly when possible.
3. Prefer Baidu document parsing for scanned PDFs.
4. Fall back to page-by-page OCR when necessary.
5. Export Markdown and JSON for downstream analysis.

## Features

- Auto-detects **text**, **scanned**, or **mixed** PDFs
- Extracts text directly from text-based PDFs
- Uses **Baidu document parsing** first for scanned PDFs
- Falls back to **page OCR** when document parsing is unavailable or fails
- Exports structured **Markdown** and **JSON** output
- Works well as the **document ingestion layer** for research workflows

## Repository Structure

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

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Z-AErIs/ocr-pdf-baidu.git
cd ocr-pdf-baidu
```

### 2. Set your Baidu OCR credentials

```bash
export BAIDU_OCR_API_KEY="..."
export BAIDU_OCR_SECRET_KEY="..."
```

Optional:

```bash
export BAIDU_OCR_BASE_URL="https://aip.baidubce.com"
export BAIDU_OCR_IMAGE_ENDPOINT="accurate_basic"
export BAIDU_OCR_LANGUAGE_TYPE="CHN_ENG"
```

## Usage

### Auto mode

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode auto --out-md ./out.md --out-json ./out.json
```

### Text-only mode

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode text --out-md ./out.md --out-json ./out.json
```

### OCR-only mode

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode ocr --out-md ./out.md --out-json ./out.json
```

### Force document parsing

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode doc --out-md ./out.md --out-json ./out.json
```

## Recommended Workflow

1. Run `scripts/detect_pdf_type.py` on a sample PDF.
2. Use `scripts/ocr_pdf.py` in `auto` mode.
3. Review the generated Markdown.
4. Feed the Markdown into your research / summary workflow.
5. Package with `dist/ocr-pdf-baidu.skill` for OpenClaw distribution.

## Outputs

- `out.md` — human-readable Markdown
- `out.json` — structured metadata and extraction results
- `dist/ocr-pdf-baidu.skill` — packaged OpenClaw skill

## Notes

- The repository is designed for OpenClaw skills.
- Baidu OCR credentials are never committed; store them in environment variables or a secret manager.
- For large PDFs, prefer document parsing first and page OCR as fallback.
- The project is optimized for Chinese investment research materials, but it also works for any PDF that needs OCR or extraction.

## Development

This project is intentionally lightweight and dependency-minimal.
If you want to modify the OCR flow, the key scripts are:

- `scripts/detect_pdf_type.py` — PDF type detection
- `scripts/ocr_pdf.py` — main orchestration logic
- `scripts/export_markdown.py` — Markdown export helper

## Contributing

Contributions are welcome.

If you find an issue or have a suggestion:

1. Open an issue
2. Propose a fix
3. Keep secrets out of the repository
4. Prefer simple, reliable changes

## License

MIT License. See [LICENSE](LICENSE).

## 中文说明

这是一个用于处理中文 PDF 的 OpenClaw skill，适合把**扫描版**或**文本型** PDF 转成可研究的 Markdown，并为后续摘要、研究和归档流程提供统一入口。

### 它支持

- 自动识别 PDF 是文本型、扫描型还是混合型
- 文本型 PDF 直接抽取正文
- 扫描型 PDF 优先使用百度文档解析
- 文档解析失败时回退到逐页 OCR
- 输出 Markdown 和 JSON，方便后续研究工作流使用

### 快速开始

```bash
cd ocr-pdf-baidu
export BAIDU_OCR_API_KEY="..."
export BAIDU_OCR_SECRET_KEY="..."
python3 scripts/ocr_pdf.py ./sample.pdf --mode auto --out-md ./out.md --out-json ./out.json
```

### 推荐流程

1. 先用 `scripts/detect_pdf_type.py` 检测 PDF 类型
2. 再用 `scripts/ocr_pdf.py` 的 `auto` 模式处理
3. 检查生成的 Markdown
4. 将 Markdown 交给你的摘要 / 研究工作流
5. 需要分发时，使用 `dist/ocr-pdf-baidu.skill` 打包成果
