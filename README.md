# OCR PDF Baidu

OpenClaw skill for converting scanned or text-based Chinese PDFs into Markdown using Baidu OCR.

## What it does

- Detects whether a PDF is text-based, scanned, or mixed.
- Extracts text directly from text-based PDFs.
- Prefers Baidu document parsing for scanned PDFs.
- Falls back to page-by-page OCR when needed.
- Exports Markdown and JSON outputs for downstream research workflows.

## Repository layout

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
