/**
 * 异步上传客户端（轮询 + 超时重试）
 * 适配后端接口：
 * - POST /api/upload/file/
 * - GET  /api/upload/status/{upload_id}/
 */
(function (global) {
  'use strict';

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function requestJson(url, options = {}) {
    const resp = await fetch(url, {
      credentials: 'include',
      ...options,
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        ...(options.headers || {}),
      },
    });

    let data;
    try {
      data = await resp.json();
    } catch (_) {
      data = { error: '服务返回非 JSON' };
    }

    if (!resp.ok) {
      const msg = data?.error || `请求失败(${resp.status})`;
      throw new Error(msg);
    }

    return data;
  }

  /**
   * 轮询上传状态
   * @param {string} statusPath - /api/upload/status/{upload_id}/
   * @param {object} opts
   */
  async function pollUploadStatus(statusPath, opts = {}) {
    const {
      timeoutMs = 120000,
      intervalMs = 1500,
      maxRetries = 3,
      onProgress,
      signal,
    } = opts;

    const start = Date.now();
    let retries = 0;

    while (true) {
      if (signal?.aborted) throw new Error('上传已取消');
      if (Date.now() - start > timeoutMs) throw new Error('上传处理超时，请稍后重试');

      try {
        const data = await requestJson(statusPath, { method: 'GET', signal });
        const st = data.status;

        if (typeof onProgress === 'function') onProgress(data);

        if (st === 'ready') return data;
        if (st === 'rejected') throw new Error(data.reason || '文件安全扫描未通过');
        if (st === 'failed') throw new Error(data.error || '文件处理失败');

        // pending / scanning
        await sleep(intervalMs);
        retries = 0;
      } catch (err) {
        if (signal?.aborted) throw err;

        // 网络波动重试
        retries += 1;
        if (retries > maxRetries) throw err;

        // 指数退避
        const backoff = intervalMs * Math.pow(2, retries - 1);
        await sleep(backoff);
      }
    }
  }

  /**
   * 上传文件（自动兼容同步/异步模式）
   * - 同步模式：直接返回 location
   * - 异步模式：先拿 pending，再轮询 status
   */
  async function uploadFileWithPolling(file, opts = {}) {
    const {
      uploadUrl = '/api/upload/file/',
      timeoutMs = 120000,
      intervalMs = 1500,
      maxRetries = 3,
      onProgress,
      signal,
    } = opts;

    const formData = new FormData();
    formData.append('file', file);

    const data = await requestJson(uploadUrl, {
      method: 'POST',
      body: formData,
      signal,
    });

    // 兼容同步接口
    if (data.location) {
      return {
        status: 'ready',
        location: data.location,
        filename: data.filename || file.name,
        size: data.size || file.size,
      };
    }

    // 异步接口
    if (data.status === 'pending' && data.status_path) {
      return pollUploadStatus(data.status_path, {
        timeoutMs,
        intervalMs,
        maxRetries,
        onProgress,
        signal,
      });
    }

    throw new Error(data.error || '上传响应格式异常');
  }

  global.UploadAsyncClient = {
    uploadFileWithPolling,
    pollUploadStatus,
  };
})(window);
