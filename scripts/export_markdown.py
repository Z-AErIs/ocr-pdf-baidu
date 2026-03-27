#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export OCR JSON results to Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_markdown(data: dict) -> str:
    src = Path(data.get("source_file", "unknown.pdf"))
    lines = [
        f"# {src.name}",
        "",
        "## 基本信息",
        f"- 文件类型：{data.get('file_type', '')}",
        f"- 页数：{data.get('pages', '')}",
        f"- 引擎：{data.get('engine', '')}",
        f"- OCR 接口：{data.get('ocr_endpoint', '')}",
    ]

    sample_meta = data.get("sample_meta") or {}
    if sample_meta:
        lines.append(f"- 检测信息：{json.dumps(sample_meta, ensure_ascii=False)}")
    lines.append("")

    for item in data.get("page_results", []):
        lines.append(f"## 第 {item.get('page', '?')} 页")
        lines.append("")
        if item.get("error"):
            lines.append(f"> OCR 错误：{item['error']}")
            lines.append("")
        text = (item.get("text") or "").strip()
        lines.append(text if text else "_(empty)_")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OCR JSON to Markdown.")
    parser.add_argument("input", type=Path, help="Input JSON file")
    parser.add_argument("--out", type=Path, default=None, help="Output Markdown file")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    markdown = build_markdown(data)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
