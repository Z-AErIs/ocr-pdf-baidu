# OCR PDF Baidu / 百度 OCR PDF 处理

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://github.com/Z-AErIs/ocr-pdf-baidu)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 一个用于将扫描版或文本型中文 PDF 转成 Markdown 的 OpenClaw skill。
>
> An OpenClaw skill for converting scanned or text-based Chinese PDFs into Markdown using Baidu OCR.

---

## 中文说明

### 项目简介

`ocr-pdf-baidu` 是一个面向 **OpenClaw** 的 PDF 处理 skill，适合将研报、投资心得、公告、截图等中文资料转成可研究的 Markdown，并输出结构化 JSON，方便后续的摘要、研究、归档和复盘流程。

它的核心目标是把“资料入口”打通：

1. 先判断 PDF 是文本型、扫描型还是混合型；
2. 文本型 PDF 直接抽取正文；
3. 扫描型 PDF 优先使用百度文档解析；
4. 文档解析失败或不适用时回退到逐页 OCR；
5. 输出 Markdown 和 JSON，供后续投研工作流继续消费。

### 核心特性

- 自动识别 PDF 是 **文本型 / 扫描型 / 混合型**
- 文本型 PDF 可直接抽取正文
- 扫描型 PDF 优先使用 **百度文档解析 / 文档格式转换**
- 文档解析失败时可回退到逐页图片 OCR
- 输出 **Markdown + JSON**，便于摘要、研究和归档
- 适合作为投研工作流中的 **资料入口层**

### 目录结构

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

### 安装

```bash
git clone https://github.com/Z-AErIs/ocr-pdf-baidu.git
cd ocr-pdf-baidu
```

### 配置环境变量

```bash
export BAIDU_OCR_API_KEY="..."
export BAIDU_OCR_SECRET_KEY="..."
```

可选配置：

```bash
export BAIDU_OCR_BASE_URL="https://aip.baidubce.com"
export BAIDU_OCR_IMAGE_ENDPOINT="accurate_basic"
export BAIDU_OCR_LANGUAGE_TYPE="CHN_ENG"
```

### 使用方式

#### 自动模式（推荐）

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode auto --out-md ./out.md --out-json ./out.json
```

#### 只抽文本型 PDF

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode text --out-md ./out.md --out-json ./out.json
```

#### 只走 OCR

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode ocr --out-md ./out.md --out-json ./out.json
```

#### 强制走文档解析

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode doc --out-md ./out.md --out-json ./out.json
```

### 推荐流程

1. 先用 `scripts/detect_pdf_type.py` 检测 PDF 类型；
2. 再用 `scripts/ocr_pdf.py --mode auto` 处理；
3. 检查生成的 Markdown；
4. 将 Markdown 交给后续摘要 / 研究工作流；
5. 如需分发，使用 `dist/ocr-pdf-baidu.skill` 作为 OpenClaw skill 包。

### 输出说明

- `out.md`：人类可读的 Markdown
- `out.json`：结构化结果和元数据
- `dist/ocr-pdf-baidu.skill`：可分发的 OpenClaw skill 包

### 开发说明

本项目保持轻量、依赖尽量少。
如果你要修改 OCR 流程，主要看以下脚本：

- `scripts/detect_pdf_type.py`：PDF 类型识别
- `scripts/ocr_pdf.py`：主流程编排
- `scripts/export_markdown.py`：Markdown 导出辅助

### 贡献

欢迎提交 Issue 或 Pull Request。

请注意：

- 不要提交真实 API Key / Secret Key
- 尽量保持实现简单、稳定、可维护
- 若你有更好的 OCR 路径或输出格式，也欢迎提出

### 许可证

MIT License。详见 [LICENSE](LICENSE)。

---

## English Overview

### Project Summary

`ocr-pdf-baidu` is an OpenClaw skill designed to turn Chinese PDFs — scanned or text-based — into research-friendly Markdown and JSON.

It is especially useful for investment reports, notes, announcements, and screenshots.

The workflow is simple:

1. Detect whether the PDF is text-based, scanned, or mixed.
2. Extract text directly when possible.
3. Prefer Baidu document parsing for scanned PDFs.
4. Fall back to page-by-page OCR when necessary.
5. Export Markdown and JSON for downstream workflows.

### Features

- Auto-detects **text / scanned / mixed** PDFs
- Extracts text directly from text-based PDFs
- Uses **Baidu document parsing** first for scanned PDFs
- Falls back to page OCR when document parsing is unavailable
- Exports structured **Markdown + JSON** output
- Works well as a **document ingestion layer** for research workflows

### Repository Structure

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

### Installation

```bash
git clone https://github.com/Z-AErIs/ocr-pdf-baidu.git
cd ocr-pdf-baidu
```

### Environment Variables

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

### Usage

#### Auto mode (recommended)

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode auto --out-md ./out.md --out-json ./out.json
```

#### Text-only mode

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode text --out-md ./out.md --out-json ./out.json
```

#### OCR-only mode

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode ocr --out-md ./out.md --out-json ./out.json
```

#### Force document parsing

```bash
python3 scripts/ocr_pdf.py ./sample.pdf --mode doc --out-md ./out.md --out-json ./out.json
```

### Recommended Workflow

1. Run `scripts/detect_pdf_type.py` on a sample PDF.
2. Use `scripts/ocr_pdf.py` in `auto` mode.
3. Review the generated Markdown.
4. Feed the Markdown into your research / summary workflow.
5. Package with `dist/ocr-pdf-baidu.skill` for OpenClaw distribution.

### Outputs

- `out.md` — human-readable Markdown
- `out.json` — structured metadata and extraction results
- `dist/ocr-pdf-baidu.skill` — packaged OpenClaw skill

### Development

This project is intentionally lightweight and dependency-minimal.
If you want to modify the OCR flow, the key scripts are:

- `scripts/detect_pdf_type.py` — PDF type detection
- `scripts/ocr_pdf.py` — main orchestration logic
- `scripts/export_markdown.py` — Markdown export helper

### Contributing

Contributions are welcome.

Please keep in mind:

- Do not commit real API keys or secrets
- Prefer simple, reliable changes
- If you have a better OCR pipeline or output format, feel free to open an issue or PR

### License

MIT License. See [LICENSE](LICENSE).
