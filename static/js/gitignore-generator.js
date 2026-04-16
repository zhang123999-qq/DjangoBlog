/**
 * Gitignore 生成器功能
 */
(function() {
    'use strict';
    
    // 复制到剪贴板
    window.copyToClipboard = function() {
        const code = document.getElementById('gitignore-code');
        if (code) {
            navigator.clipboard.writeText(code.textContent).then(function() {
                showToast('已复制到剪贴板', 'success');
            }).catch(function(err) {
                console.error('复制失败:', err);
                showToast('复制失败', 'error');
            });
        }
    };
    
    // 下载文件
    window.downloadFile = function() {
        const code = document.getElementById('gitignore-code');
        if (code) {
            const blob = new Blob([code.textContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '.gitignore';
            a.click();
            URL.revokeObjectURL(url);
        }
    };
    
    // 显示Toast通知
    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toast.style.zIndex = '9999';
        
        const bgColor = type === 'success' ? 'bg-success' : 'bg-danger';
        const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle';
        
        toast.innerHTML = `
            <div class="toast show" role="alert">
                <div class="toast-header ${bgColor} text-white">
                    <i class="bi ${icon} me-2"></i>
                    <strong class="me-auto">提示</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" onclick="this.closest('.toast-container').remove()"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
})();
