#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Detect whether a PDF is text-based, scanned/image-based, or mixed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from pypdf import PdfReader


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return "\n".join(line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def page_has_images(page) -> bool:
    try:
        resources = page.get("/Resources") or {}
        xobj = resources.get("/XObject") if hasattr(resources, "get") else None
        return bool(xobj)
    except Exception:
        return False


def detect_pdf_type(
    pdf_path: Path,
    sample_pages: int = 3,
    min_total_chars: int = 80,
    mixed_text_ratio: float = 0.35,
) -> Tuple[str, Dict[str, Any]]:
    meta: Dict[str, Any] = {
        "sample_pages": 0,
        "sampled_text_chars": 0,
        "sampled_image_pages": 0,
        "nonempty_pages": 0,
        "text_ratio": 0.0,
    }

    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        sample_n = min(sample_pages, total_pages)
        meta["sample_pages"] = sample_n
        meta["total_pages"] = total_pages

        total_chars = 0
        nonempty = 0
        image_pages = 0

        for idx in range(sample_n):
            page = reader.pages[idx]
            try:
                txt = page.extract_text() or ""
            except Exception as exc:
                meta["detect_error"] = f"page {idx + 1} extract failed: {exc}"
                return "scanned", meta

            txt = normalize_text(txt)
            chars = len(txt)
            total_chars += chars
            if chars >= 10:
                nonempty += 1
            if page_has_images(page):
                image_pages += 1

        meta["sampled_text_chars"] = total_chars
        meta["nonempty_pages"] = nonempty
        meta["sampled_image_pages"] = image_pages
        meta["text_ratio"] = round(total_chars / max(sample_n, 1), 2)

        has_text = total_chars > 0 and nonempty >= 1
        has_images = image_pages > 0

        if has_text and not has_images:
            return "text", meta
        if has_text and has_images:
            return "mixed", meta
        if not has_text and has_images:
            return "scanned", meta

        # Fallback: if we somehow extracted a tiny amount of text but sample is noisy,
        # still treat as text when there are no obvious image pages.
        if total_chars >= min_total_chars and not has_images:
            return "text", meta
        if total_chars >= max(20, int(min_total_chars * mixed_text_ratio)) and has_images:
            return "mixed", meta

        return "scanned", meta

    except Exception as exc:
        meta["detect_error"] = str(exc)
        return "scanned", meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect whether a PDF is text-based, scanned, or mixed.")
    parser.add_argument("pdf", type=Path, help="Input PDF path")
    parser.add_argument("--sample-pages", type=int, default=3)
    parser.add_argument("--min-text-chars", type=int, default=80)
    parser.add_argument("--mixed-text-ratio", type=float, default=0.35)
    args = parser.parse_args()

    file_type, meta = detect_pdf_type(
        args.pdf,
        sample_pages=args.sample_pages,
        min_total_chars=args.min_text_chars,
        mixed_text_ratio=args.mixed_text_ratio,
    )
    out = {"file": str(args.pdf), "file_type": file_type, "meta": meta}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
