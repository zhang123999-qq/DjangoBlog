# 前端接入：异步上传轮询（含超时重试）

本项目已提供 `static/js/upload-async-client.js`。

## 一、引入脚本

```html
<script src="/static/js/upload-async-client.js"></script>
```

## 二、最小接入示例

```html
<input type="file" id="uploader" />
<div id="upload-status"></div>

<script>
const input = document.getElementById('uploader');
const statusEl = document.getElementById('upload-status');

input.addEventListener('change', async () => {
  const file = input.files?.[0];
  if (!file) return;

  statusEl.textContent = '开始上传...';

  try {
    const result = await UploadAsyncClient.uploadFileWithPolling(file, {
      timeoutMs: 120000,  // 2 分钟超时
      intervalMs: 1500,   // 1.5 秒轮询
      maxRetries: 3,      // 网络重试 3 次
      onProgress: (data) => {
        statusEl.textContent = `处理状态：${data.status}`;
      }
    });

    statusEl.innerHTML = `上传成功：<a href="${result.location}" target="_blank">${result.location}</a>`;
  } catch (err) {
    statusEl.textContent = `上传失败：${err.message}`;
  }
});
</script>
```

## 三、与 TinyMCE 集成提示

- 图片仍走 `/api/upload/image/`（同步返回 `location`）
- 通用附件（如自定义按钮上传）可走 `UploadAsyncClient.uploadFileWithPolling`
- 若后端关闭异步开关，客户端无需改动，依然兼容同步返回

## 四、状态语义

- `pending`：已入队
- `scanning`：扫描中
- `ready`：已通过并转正，返回 `location`
- `rejected`：未通过安全扫描
- `failed`：任务失败
