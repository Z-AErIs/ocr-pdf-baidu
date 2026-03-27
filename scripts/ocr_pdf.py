#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Convert PDF to Markdown using Baidu OCR.

Priority:
1) Text-based PDF -> direct text extraction
2) Scanned/image-based PDF -> Baidu document parsing (preferred)
3) If document parsing fails or is unavailable -> page-by-page image OCR
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import fitz  # PyMuPDF
from pypdf import PdfReader


DOC_PARSE_SUBMIT_PATH = "/rest/2.0/brain/online/v2/paddle-vl-parser/task"
DOC_PARSE_QUERY_PATH = "/rest/2.0/brain/online/v2/paddle-vl-parser/task/query"
PAGE_OCR_DEFAULT_ENDPOINT = "accurate_basic"
MAX_DOC_PARSE_FILE_DATA_BYTES = 50 * 1024 * 1024
DOC_PARSE_MAX_WAIT_SECONDS = 300
DOC_PARSE_POLL_INTERVAL_SECONDS = 5

DONE_MARKERS = {
    "完成",
    "已完成",
    "success",
    "succeeded",
    "done",
    "finished",
    "complete",
    "completed",
}

RETRYABLE_ERROR_CODES = {"17", "18", "19", "282000", "429"}


class OCRConfigError(RuntimeError):
    pass


class OCRAPIError(RuntimeError):
    pass


@dataclass
class PageResult:
    page: int
    mode: str
    text: str
    words_result_num: int = 0
    error: str = ""


@dataclass
class PDFReport:
    source_file: str
    file_type: str  # text | scanned | mixed
    pages: int
    engine: str
    ocr_endpoint: str
    sample_meta: Dict[str, Any]
    document_text: str = ""
    document_meta: Dict[str, Any] = field(default_factory=dict)
    page_results: List[PageResult] = field(default_factory=list)


# -----------------------------
# Utilities
# -----------------------------


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: List[str] = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).rstrip()
        lines.append(line)
    return "\n".join(lines).strip()


def ensure_parent_dir(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise OCRConfigError(f"缺少环境变量: {name}")
    return value or ""


def build_markdown(report: PDFReport) -> str:
    src = Path(report.source_file)
    lines: List[str] = []

    lines.append(f"# {src.name}")
    lines.append("")
    lines.append("## 基本信息")
    lines.append(f"- 文件类型：{report.file_type}")
    lines.append(f"- 页数：{report.pages}")
    lines.append(f"- 引擎：{report.engine}")
    lines.append(f"- OCR 接口：{report.ocr_endpoint or '-'}")
    if report.sample_meta:
        lines.append(f"- 检测信息：{json.dumps(report.sample_meta, ensure_ascii=False)}")
    if report.document_meta:
        lines.append(f"- 文档解析信息：{json.dumps(report.document_meta, ensure_ascii=False)}")
    lines.append("")

    if report.document_text:
        lines.append("## 文档解析结果")
        lines.append("")
        lines.append(report.document_text.strip())
        lines.append("")
    elif report.page_results:
        for item in report.page_results:
            lines.append(f"## 第 {item.page} 页")
            lines.append("")
            if item.error:
                lines.append(f"> OCR 错误：{item.error}")
                lines.append("")
            lines.append(item.text.strip() if item.text.strip() else "_(empty)_")
            lines.append("")
    else:
        lines.append("_(empty)_")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def payload_sections(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    if isinstance(payload, dict):
        sections.append(payload)
        for key in ("result", "data"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                sections.append(nested)
    return sections


def first_payload_value(payload: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for section in payload_sections(payload):
        for key in keys:
            value = section.get(key)
            if value not in (None, "", [], {}):
                return value
    return default


def summarize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_id": first_payload_value(payload, "task_id", "taskId", default=""),
        "task_error": first_payload_value(payload, "task_error", "error_msg", default=""),
        "markdown_url": first_payload_value(payload, "markdown_url", "markdownUrl", default=""),
        "parse_result_url": first_payload_value(payload, "parse_result_url", "parseResultUrl", default=""),
        "status": first_payload_value(payload, "status", "task_status", default=""),
        "ret_msg": first_payload_value(payload, "ret_msg", "message", default=""),
    }


# -----------------------------
# HTTP helpers (stdlib only)
# -----------------------------


def perform_http_request(
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 60,
) -> Tuple[int, bytes, Dict[str, str]]:
    full_url = url
    if params:
        query = urlencode(params, doseq=True)
        full_url = f"{url}&{query}" if "?" in url else f"{url}?{query}"

    body = None
    if data is not None:
        body = urlencode(data, doseq=True).encode("utf-8")

    req = Request(full_url, data=body, method=method.upper())
    req.add_header("Accept", "application/json, text/plain, */*")
    if body is not None:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    for key, value in (headers or {}).items():
        req.add_header(key, value)

    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read(), dict(resp.headers.items())
    except HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers.items()) if exc.headers else {}
    except URLError as exc:
        raise OCRAPIError(str(exc)) from exc


def decode_bytes(body: bytes) -> str:
    return body.decode("utf-8", errors="replace").strip()


def request_json_with_retry(
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
    retries: int = 3,
    backoff: float = 1.5,
) -> Dict[str, Any]:
    last_error: Optional[str] = None

    for attempt in range(retries):
        status, body, _headers = perform_http_request(method, url, params=params, data=data, timeout=timeout)
        text = decode_bytes(body)
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {}

        error_code = str(payload.get("error_code", "")) if isinstance(payload, dict) else ""
        ok = status == 200 and not error_code
        retryable = status >= 500 or status in {408, 429} or error_code in RETRYABLE_ERROR_CODES

        if ok:
            return payload

        last_error = f"HTTP {status} / payload={payload} / body={text[:1000]}"
        if attempt < retries - 1 and retryable:
            time.sleep(backoff ** attempt)
            continue
        raise OCRAPIError(last_error)

    raise OCRAPIError(last_error or "unknown OCR error")


def request_text_with_retry(
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
    retries: int = 3,
    backoff: float = 1.5,
) -> str:
    last_error: Optional[str] = None

    for attempt in range(retries):
        try:
            status, body, _headers = perform_http_request(method, url, params=params, data=data, timeout=timeout)
            if status >= 400:
                raise OCRAPIError(f"HTTP {status}: {decode_bytes(body)[:1000]}")
            return decode_bytes(body)
        except OCRAPIError as exc:
            last_error = str(exc)
            if attempt < retries - 1:
                time.sleep(backoff ** attempt)
                continue
            raise

    raise OCRAPIError(last_error or "failed to fetch text")


# -----------------------------
# PDF type detection
# -----------------------------


def page_has_images(page) -> bool:
    try:
        resources = page.get("/Resources") or {}
        xobj = resources.get("/XObject") if hasattr(resources, "get") else None
        return bool(xobj)
    except Exception:
        return False


def detect_pdf_type(pdf_path: Path, sample_pages: int = 3, min_total_chars: int = 80, mixed_text_ratio: float = 0.35) -> Tuple[str, Dict[str, Any]]:
    meta: Dict[str, Any] = {"sample_pages": 0, "sampled_text_chars": 0, "sampled_image_pages": 0, "nonempty_pages": 0, "text_ratio": 0.0}

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

        if total_chars >= min_total_chars and not has_images:
            return "text", meta
        if total_chars >= max(20, int(min_total_chars * mixed_text_ratio)) and has_images:
            return "mixed", meta

        return "scanned", meta

    except Exception as exc:
        meta["detect_error"] = str(exc)
        return "scanned", meta


# -----------------------------
# Text extraction
# -----------------------------


def extract_text_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> List[PageResult]:
    reader = PdfReader(str(pdf_path))
    results: List[PageResult] = []

    for page_no, page in enumerate(reader.pages, start=1):
        if max_pages is not None and page_no > max_pages:
            break

        try:
            txt = normalize_text(page.extract_text() or "")
            results.append(PageResult(page=page_no, mode="text", text=txt, words_result_num=len(txt)))
        except Exception as exc:
            results.append(PageResult(page=page_no, mode="text", text="", words_result_num=0, error=str(exc)))

    return results


# -----------------------------
# Baidu OCR auth + doc parsing
# -----------------------------


def fetch_access_token(base_url: str, api_key: str, secret_key: str) -> str:
    url = base_url.rstrip("/") + "/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
    payload = request_json_with_retry("GET", url, params=params, timeout=30, retries=3)
    token = payload.get("access_token")
    if not token:
        raise OCRAPIError(f"获取 token 失败：{payload}")
    return str(token)


def submit_doc_parse_task(base_url: str, access_token: str, pdf_path: Path, *, file_url: Optional[str] = None) -> Dict[str, Any]:
    url = base_url.rstrip("/") + DOC_PARSE_SUBMIT_PATH
    params = {"access_token": access_token}

    data: Dict[str, Any] = {"file_name": pdf_path.name}
    if file_url:
        data["file_url"] = file_url
    else:
        data["file_data"] = base64.b64encode(pdf_path.read_bytes()).decode("utf-8")

    return request_json_with_retry("POST", url, params=params, data=data, timeout=120, retries=3)


def query_doc_parse_task(base_url: str, access_token: str, task_id: str) -> Dict[str, Any]:
    url = base_url.rstrip("/") + DOC_PARSE_QUERY_PATH
    params = {"access_token": access_token}
    data = {"task_id": task_id}
    return request_json_with_retry("POST", url, params=params, data=data, timeout=60, retries=3)


def _is_doc_parse_done(payload: Dict[str, Any]) -> bool:
    if first_payload_value(payload, "markdown_url", "markdownUrl", default="") or first_payload_value(payload, "parse_result_url", "parseResultUrl", default=""):
        return True

    status_fields = [
        first_payload_value(payload, "task_status", default=""),
        first_payload_value(payload, "ret_msg", default=""),
        first_payload_value(payload, "status", default=""),
        first_payload_value(payload, "message", default=""),
    ]
    status_text = " ".join(str(v) for v in status_fields if v is not None).strip().lower()
    return any(marker in status_text for marker in DONE_MARKERS)


def wait_for_doc_parse_markdown(base_url: str, access_token: str, pdf_path: Path, *, file_url: Optional[str] = None, poll_interval: int = DOC_PARSE_POLL_INTERVAL_SECONDS, timeout_seconds: int = DOC_PARSE_MAX_WAIT_SECONDS) -> Tuple[str, Dict[str, Any]]:
    submit_payload = submit_doc_parse_task(base_url, access_token, pdf_path, file_url=file_url)

    task_id = first_payload_value(submit_payload, "task_id", "taskId", default="")
    if not task_id:
        raise OCRAPIError(f"文档解析提交失败：{submit_payload}")

    deadline = time.time() + timeout_seconds
    last_payload: Dict[str, Any] = submit_payload

    while time.time() < deadline:
        payload = query_doc_parse_task(base_url, access_token, str(task_id))
        last_payload = payload

        if payload.get("task_error"):
            raise OCRAPIError(f"文档解析失败：{payload.get('task_error')}")

        if _is_doc_parse_done(payload):
            markdown_url = str(first_payload_value(payload, "markdown_url", "markdownUrl", default="") or "")
            parse_result_url = str(first_payload_value(payload, "parse_result_url", "parseResultUrl", default="") or "")
            if markdown_url:
                markdown = request_text_with_retry("GET", markdown_url, timeout=60, retries=3)
            elif parse_result_url:
                markdown = request_text_with_retry("GET", parse_result_url, timeout=60, retries=3)
            else:
                markdown = json.dumps(payload, ensure_ascii=False, indent=2)

            return markdown, {
                "task_id": str(task_id),
                "submit_result": summarize_payload(submit_payload),
                "query_result": summarize_payload(payload),
                "markdown_url": markdown_url,
                "parse_result_url": parse_result_url,
            }

        time.sleep(poll_interval)

    raise OCRAPIError(f"文档解析超时：task_id={task_id}，最后状态={summarize_payload(last_payload)}")


# -----------------------------
# Page OCR fallback
# -----------------------------


def ocr_image_bytes(base_url: str, access_token: str, image_endpoint: str, image_bytes: bytes, language_type: str = "CHN_ENG", detect_direction: bool = True) -> Tuple[str, Dict[str, Any]]:
    url = base_url.rstrip("/") + f"/rest/2.0/ocr/v1/{image_endpoint.lstrip('/')}"
    params = {"access_token": access_token}
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    data = {"image": image_b64, "language_type": language_type, "detect_direction": "true" if detect_direction else "false"}

    payload = request_json_with_retry("POST", url, params=params, data=data, timeout=120, retries=3)

    words_result = payload.get("words_result", []) or []
    lines = []
    for item in words_result:
        words = item.get("words", "")
        if words:
            lines.append(words)

    text = normalize_text("\n".join(lines))
    return text, payload


def render_page_png_bytes(doc: fitz.Document, page_index: int, zoom: float = 2.2) -> bytes:
    page = doc.load_page(page_index)
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    return pix.tobytes("png")


def ocr_scanned_pdf_by_pages(pdf_path: Path, *, base_url: str, access_token: str, image_endpoint: str, language_type: str, zoom: float = 2.2, max_pages: Optional[int] = None) -> List[PageResult]:
    results: List[PageResult] = []
    doc = fitz.open(str(pdf_path))

    try:
        total_pages = doc.page_count
        limit = min(total_pages, max_pages) if max_pages is not None else total_pages

        for page_index in range(limit):
            page_no = page_index + 1
            try:
                img_bytes = render_page_png_bytes(doc, page_index, zoom=zoom)
                text, payload = ocr_image_bytes(base_url=base_url, access_token=access_token, image_endpoint=image_endpoint, image_bytes=img_bytes, language_type=language_type, detect_direction=True)
                words_result_num = int(payload.get("words_result_num", 0) or len(payload.get("words_result", []) or []))
                results.append(PageResult(page=page_no, mode="ocr", text=text, words_result_num=words_result_num))
            except Exception as exc:
                results.append(PageResult(page=page_no, mode="ocr", text="", words_result_num=0, error=str(exc)))
    finally:
        doc.close()

    return results


# -----------------------------
# Orchestration
# -----------------------------


def should_use_file_data(pdf_path: Path) -> bool:
    return pdf_path.stat().st_size <= MAX_DOC_PARSE_FILE_DATA_BYTES


def process_scanned_pdf(pdf_path: Path, *, base_url: str, access_token: str, image_endpoint: str, language_type: str, zoom: float, max_pages: Optional[int], file_url: Optional[str], prefer_doc_parse: bool) -> Tuple[str, str, Dict[str, Any], str, List[PageResult]]:
    """Return (engine, ocr_endpoint, document_meta, document_text, page_results)."""

    document_meta: Dict[str, Any] = {}

    if prefer_doc_parse:
        if file_url or should_use_file_data(pdf_path):
            try:
                markdown, doc_meta = wait_for_doc_parse_markdown(base_url=base_url, access_token=access_token, pdf_path=pdf_path, file_url=file_url)
                document_meta.update(doc_meta)
                return "baidu_doc_parse", "paddle-vl-parser/task", document_meta, markdown, []
            except Exception as exc:
                document_meta["doc_parse_error"] = str(exc)
        else:
            document_meta["doc_parse_skipped"] = "pdf too large for file_data and no file_url provided"

    page_results = ocr_scanned_pdf_by_pages(pdf_path, base_url=base_url, access_token=access_token, image_endpoint=image_endpoint, language_type=language_type, zoom=zoom, max_pages=max_pages)
    return "baidu_ocr", image_endpoint, document_meta, "", page_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect PDF type and OCR scanned PDFs with Baidu OCR.")
    parser.add_argument("pdf", type=Path, help="输入 PDF 文件路径")
    parser.add_argument("--mode", choices=["auto", "text", "doc", "ocr"], default="auto", help="处理模式")
    parser.add_argument("--file-url", default="", help="可访问的 PDF URL；当本地 PDF 过大时可用于文档解析")
    parser.add_argument("--out-md", type=Path, default=None, help="输出 Markdown 文件")
    parser.add_argument("--out-json", type=Path, default=None, help="输出 JSON 文件")
    parser.add_argument("--max-pages", type=int, default=None, help="最多处理前 N 页（仅文本抽取/页级 OCR）")
    parser.add_argument("--sample-pages", type=int, default=3, help="自动检测时采样页数")
    parser.add_argument("--min-text-chars", type=int, default=80, help="判定文本型 PDF 的最小采样字符数")
    parser.add_argument("--zoom", type=float, default=2.2, help="扫描页渲图缩放倍数")
    parser.add_argument("--base-url", default=get_env("BAIDU_OCR_BASE_URL", "https://aip.baidubce.com"), help="百度 OCR 基础 URL")
    parser.add_argument("--image-endpoint", default=get_env("BAIDU_OCR_IMAGE_ENDPOINT", PAGE_OCR_DEFAULT_ENDPOINT), help="图片 OCR 接口名")
    parser.add_argument("--language-type", default=get_env("BAIDU_OCR_LANGUAGE_TYPE", "CHN_ENG"), help="语言类型")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.pdf.exists():
        print(f"[ERR] 文件不存在: {args.pdf}", file=sys.stderr)
        return 2

    report_meta: Dict[str, Any] = {}
    file_type, report_meta = detect_pdf_type(args.pdf, sample_pages=args.sample_pages, min_total_chars=args.min_text_chars)
    total_pages = len(PdfReader(str(args.pdf)).pages)

    if args.mode == "text" or (args.mode == "auto" and file_type == "text"):
        page_results = extract_text_pdf(args.pdf, max_pages=args.max_pages)
        report = PDFReport(source_file=str(args.pdf), file_type="text", pages=total_pages, engine="pypdf", ocr_endpoint="", sample_meta=report_meta, page_results=page_results)
    else:
        api_key = get_env("BAIDU_OCR_API_KEY", required=True)
        secret_key = get_env("BAIDU_OCR_SECRET_KEY", required=True)
        access_token = fetch_access_token(args.base_url, api_key, secret_key)

        prefer_doc_parse = args.mode in {"auto", "doc"}
        engine, ocr_endpoint, document_meta, document_text, page_results = process_scanned_pdf(
            args.pdf,
            base_url=args.base_url,
            access_token=access_token,
            image_endpoint=args.image_endpoint,
            language_type=args.language_type,
            zoom=args.zoom,
            max_pages=args.max_pages,
            file_url=args.file_url or None,
            prefer_doc_parse=prefer_doc_parse,
        )

        report = PDFReport(source_file=str(args.pdf), file_type=file_type, pages=total_pages, engine=engine, ocr_endpoint=ocr_endpoint, sample_meta=report_meta, document_text=document_text, document_meta=document_meta, page_results=page_results)

    markdown = build_markdown(report)
    json_obj = {**asdict(report), "page_results": [asdict(x) for x in report.page_results]}

    if args.out_md:
        ensure_parent_dir(args.out_md)
        args.out_md.write_text(markdown, encoding="utf-8")

    if args.out_json:
        ensure_parent_dir(args.out_json)
        args.out_json.write_text(json.dumps(json_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    sys.stdout.write(markdown)
    print(f"[OK] {args.pdf.name}: {file_type} -> {report.engine}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
