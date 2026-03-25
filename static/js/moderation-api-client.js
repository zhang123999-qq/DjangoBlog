/**
 * Moderation API 客户端（错误码映射版）
 */
(function (global) {
  'use strict';

  const ERROR_MESSAGE_MAP = {
    MODERATION_PERMISSION_DENIED: '你没有审核权限。',
    MODERATION_INVALID_CONTENT_TYPE: '不支持的审核内容类型。',
    MODERATION_CONTENT_NOT_FOUND: '审核对象不存在或已被处理。',
    MODERATION_APPROVE_FAILED: '审核通过失败，请稍后重试。',
    MODERATION_REJECT_FAILED: '审核拒绝失败，请稍后重试。',
    MODERATION_API_RATE_LIMITED: '审核请求太频繁，请稍后再试。',
    MODERATION_API_CONCURRENCY_LIMITED: '当前审核任务较多，请稍后再试。',
  };

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function resolveErrorMessage(code, fallback) {
    if (code && ERROR_MESSAGE_MAP[code]) return ERROR_MESSAGE_MAP[code];
    return fallback || '请求失败，请稍后重试。';
  }

  function toApiError(payload, statusCode) {
    const code = payload?.error_code || null;
    const msg = resolveErrorMessage(code, payload?.error || payload?.message || `请求失败(${statusCode || 0})`);
    const err = new Error(msg);
    err.code = code;
    err.status = statusCode || 0;
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
      data = { error: '服务返回非 JSON' };
    }

    if (!resp.ok) {
      throw toApiError(data, resp.status);
    }

    return data;
  }

  function approve(contentType, contentId) {
    return requestJson(`/api/moderation/approve/${contentType}/${contentId}/`, {
      method: 'POST',
    });
  }

  function reject(contentType, contentId, reviewNote) {
    return requestJson(`/api/moderation/reject/${contentType}/${contentId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ review_note: reviewNote || '' }),
    });
  }

  function getErrorMessage(err) {
    if (!err) return '请求失败，请稍后重试。';
    if (err.code) return resolveErrorMessage(err.code, err.message);
    return err.message || '请求失败，请稍后重试。';
  }

  global.ModerationApiClient = {
    approve,
    reject,
    getErrorMessage,
    ERROR_MESSAGE_MAP,
  };
})(window);
