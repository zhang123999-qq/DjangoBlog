/**
 * IP检测工具功能
 */
(function() {
    'use strict';
    
    // 自动提交表单
    function initIPDetector() {
        const autoForm = document.getElementById('auto-form');
        const ipDisplay = document.getElementById('ip-display');
        
        // 如果没有结果，自动提交表单
        if (autoForm && !ipDisplay) {
            autoForm.submit();
        }
    }
    
    // 复制IP
    window.copyIP = function() {
        const ipElement = document.getElementById('ip-display');
        if (!ipElement) return;
        
        const ip = ipElement.textContent;
        navigator.clipboard.writeText(ip).then(function() {
            showToast('IP地址已复制到剪贴板');
        }).catch(function(err) {
            console.error('复制失败:', err);
            showToast('复制失败，请手动复制', 'error');
        });
    };
    
    // 显示Toast通知
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = 'position-fixed bottom-0 end-0 p-3';
        toast.style.zIndex = '9999';
        
        const bgColor = type === 'success' ? 'bg-success' : 'bg-danger';
        const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle';
        
        toast.innerHTML = `
            <div class="toast show" role="alert">
                <div class="toast-header ${bgColor} text-white">
                    <i class="bi ${icon} me-2"></i>
                    <strong class="me-auto">${type === 'success' ? '成功' : '错误'}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" onclick="this.closest('.position-fixed').remove()"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initIPDetector);
    } else {
        initIPDetector();
    }
})();
