# 百度文档解析参考

## 目的
把扫描 PDF 转成可研究的 Markdown，适合整份文档优先处理。

## 官方接口
- 提交任务：`https://aip.baidubce.com/rest/2.0/brain/online/v2/paddle-vl-parser/task`
- 查询任务：`https://aip.baidubce.com/rest/2.0/brain/online/v2/paddle-vl-parser/task/query`

## 请求字段
- `file_data`：PDF base64 数据
- `file_url`：可访问的 PDF URL
- `file_name`：文件名，必须保留后缀
- `language_type`：通常可不传

## 文件限制
- PDF 文档最大支持 500 页
- 文件大小超过 50MB 时，优先走 `file_url`
- 文档大小上限可到 100MB 级别（以官方文档为准）

## 结果字段
- `task_id`
- `task_error`
- `markdown_url`
- `parse_result_url`

## 调用方式
1. 获取 access token。
2. 提交文档解析任务，拿到 `task_id`。
3. 每 5~10 秒轮询一次结果。
4. 任务完成后读取 `markdown_url` 或 `parse_result_url`。

## 性能与限流
- 提交接口 QPS 约为 2。
- 查询接口 QPS 约为 10。
- 批处理时要加退避和重试。
