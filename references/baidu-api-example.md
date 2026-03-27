# 百度 OCR API 示例

下面给的是这个 skill 的推荐用法：先跑 skill，再按需要看原始接口。

## 1. 推荐的技能调用方式

```bash
export BAIDU_OCR_API_KEY="..."
export BAIDU_OCR_SECRET_KEY="..."

# 文本型 PDF -> 直接抽取
python scripts/ocr_pdf.py ./sample.pdf --mode text --out-md ./out.md --out-json ./out.json

# 扫描件 PDF -> 先尝试文档解析，失败后页级 OCR 兜底
python scripts/ocr_pdf.py ./scanned.pdf --mode auto --out-md ./out.md --out-json ./out.json

# 如果 PDF 太大，且你有可访问的文件 URL，可以强制文档解析
python scripts/ocr_pdf.py ./scanned.pdf --mode doc --file-url "https://example.com/scanned.pdf" --out-md ./out.md
```

## 2. 文档解析接口流程

这是最适合扫描 PDF 的主路径：

1. 获取 access token。
2. 提交任务到文档解析接口。
3. 轮询 task_id。
4. 读取 `markdown_url` 或 `parse_result_url`。

### 提交流程示意

```python
import base64
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://aip.baidubce.com"
API_KEY = "..."
SECRET_KEY = "..."
PDF_PATH = Path("./sample.pdf")


def http_json(method, url, params=None, data=None):
    if params:
        q = urlencode(params)
        url = f"{url}&{q}" if "?" in url else f"{url}?{q}"
    body = urlencode(data).encode() if data else None
    req = Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def get_token():
    return http_json(
        "GET",
        BASE + "/oauth/2.0/token",
        params={
            "grant_type": "client_credentials",
            "client_id": API_KEY,
            "client_secret": SECRET_KEY,
        },
    )["access_token"]


def submit_doc_parse(token):
    return http_json(
        "POST",
        BASE + "/rest/2.0/brain/online/v2/paddle-vl-parser/task",
        params={"access_token": token},
        data={
            "file_name": PDF_PATH.name,
            "file_data": base64.b64encode(PDF_PATH.read_bytes()).decode(),
        },
    )


def poll_doc_parse(token, task_id):
    while True:
        result = http_json(
            "POST",
            BASE + "/rest/2.0/brain/online/v2/paddle-vl-parser/task/query",
            params={"access_token": token},
            data={"task_id": task_id},
        )
        if result.get("markdown_url"):
            return result
        time.sleep(5)


token = get_token()
submit_result = submit_doc_parse(token)
task_id = submit_result["task_id"]
final_result = poll_doc_parse(token, task_id)
print(final_result.get("markdown_url") or final_result.get("parse_result_url"))
```

## 3. 页级 OCR 兜底

当文档解析不可用时，回退到逐页图片 OCR：

```bash
python scripts/ocr_pdf.py ./scanned.pdf --mode ocr --out-md ./out.md --out-json ./out.json
```

这会先把每页渲染成图片，再调用百度通用/高精度 OCR 接口。

## 4. 你应该优先用哪条

- 想直接研究整份扫描 PDF：优先 `--mode auto` / `--mode doc`
- 想快速验证接口连通性：先跑一个小 PDF
- 想确认页级 OCR 的回退链路：用 `--mode ocr`
