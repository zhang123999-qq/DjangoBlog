/**
 * Moderation API 客户端
 * 
 * 依赖: utils.js (getCookie, requestJson, resolveErrorMessage)
 * 在模板中引入顺序: utils.js → moderation-api-client.js
 */
(function (global) {
  'use strict';

  /**
   * 错误码 → 中文提示映射表
   */
  const ERROR_MESSAGE_MAP = {
    MODERATION_PERMISSION_DENIED: '你没有审核权限。',
    MODERATION_INVALID_CONTENT_TYPE: '不支持的审核内容类型。',
    MODERATION_CONTENT_NOT_FOUND: '审核对象不存在或已被处理。',
    MODERATION_APPROVE_FAILED: '审核通过失败，请稍后重试。',
    MODERATION_REJECT_FAILED: '审核拒绝失败，请稍后重试。',
    MODERATION_API_RATE_LIMITED: '审核请求太频繁，请稍后再试。',
    MODERATION_API_CONCURRENCY_LIMITED: '当前审核任务较多，请稍后再试。',
  };

  /**
   * 带错误码映射的错误解析
   * @param {string|null} code - 错误码
   * @param {string} fallback - 备用提示信息
   * @returns {string} 中文错误信息
   */
  function resolveModerationError(code, fallback) {
    if (code && ERROR_MESSAGE_MAP[code]) return ERROR_MESSAGE_MAP[code];
    return fallback || '请求失败，请稍后重试。';
  }

  /**
   * 构建 API 错误对象
   */
  function toApiError(payload, statusCode) {
    const code = payload?.error_code || null;
    const msg = resolveModerationError(code, payload?.error || payload?.message || `请求失败(${statusCode || 0})`);
    const err = new Error(msg);
    err.code = code;
    err.status = statusCode || 0;
    err.raw = payload;
    return err;
  }

  /**
   * 审核通过
   * @param {string} contentType - 内容类型
   * @param {string} contentId - 内容 ID
   */
  async function approve(contentType, contentId) {
    try {
      return await requestJson(`/api/moderation/approve/${contentType}/${contentId}/`, { method: 'POST' });
    } catch (err) {
      throw toApiError(err.raw || { error: err.message }, err.status || 0);
    }
  }

  /**
   * 审核拒绝
   * @param {string} contentType - 内容类型
   * @param {string} contentId - 内容 ID
   * @param {string} reviewNote - 审核备注
   */
  async function reject(contentType, contentId, reviewNote) {
    try {
      return await requestJson(`/api/moderation/reject/${contentType}/${contentId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_note: reviewNote || '' }),
      });
    } catch (err) {
      throw toApiError(err.raw || { error: err.message }, err.status || 0);
    }
  }

  /**
   * 获取审核错误消息
   */
  function getErrorMessage(err) {
    if (!err) return '请求失败，请稍后重试。';
    if (err.code) return resolveModerationError(err.code, err.message);
    return err.message || '请求失败，请稍后重试。';
  }

  // 暴露全局 API
  global.ModerationApiClient = {
    approve,
    reject,
    getErrorMessage,
    ERROR_MESSAGE_MAP,
  };
})(window);
