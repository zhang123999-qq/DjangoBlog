/**
 * DjangoBlog 公共工具函数库
 * 
 * 提供跨模块共享的通用函数，避免重复定义。
 * 此文件应在所有需要 JS 交互的页面中引入。
 */

'use strict';

// ============================================================
// 1. CSRF Token 获取
// ============================================================

/**
 * 从 Cookie 中获取 CSRF Token
 * @returns {string} CSRF Token 值
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // 检查 cookie 名称是否匹配（带 = 号前缀比较）
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * 设置 fetch 请求的 CSRF 相关 headers
 * @param {Headers} headers - Fetch Headers 对象
 */
function setCSRFHeaders(headers) {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        headers.set('X-CSRFToken', csrfToken);
        headers.set('X-Requested-With', 'XMLHttpRequest');
    }
}

// ============================================================
// 2. 错误处理
// ============================================================

/**
 * 解析错误对象为可读字符串
 * @param {any} error - 错误对象
 * @returns {string} 错误信息
 */
function resolveErrorMessage(error) {
    if (error instanceof Error) {
        return error.message;
    }
    if (typeof error === 'string') {
        return error;
    }
    if (error && typeof error === 'object') {
        // 尝试从 response 中提取错误信息
        if (error.detail) return error.detail;
        if (error.message) return error.message;
        if (error.errors) return Object.values(error.errors).flat().join(', ');
        return JSON.stringify(error);
    }
    return String(error);
}

/**
 * 获取错误消息（兼容多种格式）
 * @param {any} error - 错误对象
 * @returns {string} 错误信息
 */
function getErrorMessage(error) {
    return resolveErrorMessage(error);
}

// ============================================================
// 3. 通用 Fetch 请求
// ============================================================

/**
 * 标准化 JSON Fetch 请求
 * @param {string} url - 请求 URL
 * @param {Object} options - fetch 选项
 * @returns {Promise<any>} 解析后的响应
 */
async function requestJson(url, options = {}) {
    try {
        const headers = new Headers(options.headers || {});
        headers.set('Content-Type', 'application/json');
        headers.set('Accept', 'application/json');
        setCSRFHeaders(headers);
        
        const response = await fetch(url, {
            ...options,
            headers: headers,
        });
        
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Expected JSON response, got: ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            const errorMessage = getErrorMessage(data);
            throw new Error(`API Error ${response.status}: ${errorMessage}`);
        }
        
        return data;
    } catch (error) {
        // 捕获网络错误、JSON 解析错误等
        if (error instanceof TypeError && error.message === 'Failed to fetch') {
            throw new Error('网络连接失败，请检查网络设置');
        }
        throw error;
    }
}

// ============================================================
// 4. Toast 通知（全局）
// ============================================================

/**
 * 显示 Toast 通知
 * @param {string} message - 通知消息
 * @param {string} type - 类型: success/error/warning/info
 * @param {number} duration - 显示时长 (ms)
 */
function showToast(message, type = 'success', duration = 3000) {
    if (window.showToast) {
        window.showToast(message, type, duration);
    } else {
        // Fallback: 使用原生 alert
        alert(message);
    }
}
