/**
 * 异步上传客户端（轮询 + 超时重试 + 错误码映射）
 * 适配后端接口：
 * - POST /api/upload/file/
 * - GET  /api/upload/status/{upload_id}/
 */
(function (global) {
  'use strict';

  const ERROR_MESSAGE_MAP = {
    UPLOAD_NO_FILE: '未检测到文件，请重新选择。',
    UPLOAD_IMAGE_TOO_LARGE: '图片不能超过 5MB，请压缩后再上传。',
    UPLOAD_FILE_TOO_LARGE: '文件不能超过 10MB，请压缩后再上传。',
    UPLOAD_IMAGE_TYPE_NOT_ALLOWED: '图片格式不支持，请使用 jpg/png/gif/webp。',
    UPLOAD_IMAGE_MAGIC_INVALID: '图片文件损坏或格式异常，请更换文件。',
    UPLOAD_FILE_TYPE_DENIED: '该文件类型存在安全风险，已禁止上传。',
    UPLOAD_FILE_EXT_NOT_ALLOWED: '该文件类型不在允许列表中。',
    UPLOAD_FILE_MAGIC_DENIED: '检测到危险文件特征，上传已拦截。',
    UPLOAD_SECURITY_SCAN_REJECTED: '文件未通过安全扫描，请更换文件后重试。',
    UPLOAD_TASK_NOT_FOUND: '上传任务不存在或已过期，请重新上传。',
    UPLOAD_SAVE_FAILED: '上传失败，请稍后重试。',
  };

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function resolveErrorMessage(errorCode, fallbackMessage) {
    if (errorCode && ERROR_MESSAGE_MAP[errorCode]) {
      return ERROR_MESSAGE_MAP[errorCode];
    }
    return fallbackMessage || '请求失败，请稍后重试。';
  }

  function toUploadError(payload, fallbackStatus) {
    const status = payload?.statusCode || payload?.status || fallbackStatus || 0;
    const code = payload?.error_code || payload?.code || null;
    const message = resolveErrorMessage(code, payload?.error || payload?.message || `请求失败(${status})`);
    const err = new Error(message);
    err.code = code;
    err.status = status;
    err.raw = payload;
    return err;
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
      data = { error: '服务返回非 JSON', statusCode: resp.status };
    }

    if (!resp.ok) {
      if (typeof data === 'object' && data) data.statusCode = resp.status;
      throw toUploadError(data, resp.status);
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
      if (signal?.aborted) {
        const aborted = new Error('上传已取消');
        aborted.code = 'UPLOAD_ABORTED';
        throw aborted;
      }
      if (Date.now() - start > timeoutMs) {
        const timeoutErr = new Error('上传处理超时，请稍后重试');
        timeoutErr.code = 'UPLOAD_TIMEOUT';
        throw timeoutErr;
      }

      try {
        const data = await requestJson(statusPath, { method: 'GET', signal });
        const st = data.status;

        if (typeof onProgress === 'function') onProgress(data);

        if (st === 'ready') return data;
        if (st === 'rejected') {
          throw toUploadError(
            {
              error_code: data.error_code || 'UPLOAD_SECURITY_SCAN_REJECTED',
              error: data.reason || data.error || '文件安全扫描未通过',
              statusCode: 400,
            },
            400,
          );
        }
        if (st === 'failed') {
          throw toUploadError(
            {
              error_code: data.error_code || 'UPLOAD_SAVE_FAILED',
              error: data.error || '文件处理失败',
              statusCode: 500,
            },
            500,
          );
        }

        // pending / scanning
        await sleep(intervalMs);
        retries = 0;
      } catch (err) {
        if (signal?.aborted) throw err;

        retries += 1;
        if (retries > maxRetries) throw err;

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

    if (data.location) {
      return {
        status: 'ready',
        location: data.location,
        filename: data.filename || file.name,
        size: data.size || file.size,
      };
    }

    if (data.status === 'pending' && data.status_path) {
      return pollUploadStatus(data.status_path, {
        timeoutMs,
        intervalMs,
        maxRetries,
        onProgress,
        signal,
      });
    }

    throw toUploadError(
      {
        error_code: data.error_code || 'UPLOAD_SAVE_FAILED',
        error: data.error || '上传响应格式异常',
        statusCode: 500,
      },
      500,
    );
  }

  function getErrorMessage(err) {
    if (!err) return '上传失败，请稍后重试。';
    if (err.code) return resolveErrorMessage(err.code, err.message);
    return err.message || '上传失败，请稍后重试。';
  }

  global.UploadAsyncClient = {
    uploadFileWithPolling,
    pollUploadStatus,
    getErrorMessage,
    ERROR_MESSAGE_MAP,
  };
})(window);
