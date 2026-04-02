// 全局 JavaScript 代码

// 文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 复制到剪贴板功能（优先使用 Clipboard API，回退到 execCommand）
    window.copyToClipboard = async function(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        let text;
        if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
            text = element.value;
        } else {
            text = element.textContent || element.innerText;
        }

        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
            } else {
                // 回退方案
                const tempElement = document.createElement('textarea');
                tempElement.value = text;
                tempElement.style.position = 'fixed';
                tempElement.style.left = '-9999px';
                document.body.appendChild(tempElement);
                tempElement.select();
                document.execCommand('copy');
                document.body.removeChild(tempElement);
            }
            showToast('已复制到剪贴板');
        } catch (err) {
            console.error('复制失败:', err);
            showToast('复制失败，请手动复制');
        }
    };

    // 显示Toast消息
    function showToast(message) {
        // 检查是否已存在toast元素
        let toast = document.getElementById('site-toast');
        if (!toast) {
            // 创建toast元素
            toast = document.createElement('div');
            toast.id = 'site-toast';
            toast.className = 'position-fixed top-20 right-0 m-3 p-3 bg-dark text-white rounded shadow-lg z-50';
            toast.style.maxWidth = '300px';
            document.body.appendChild(toast);
        }
        
        // 设置消息内容
        toast.textContent = message;
        
        // 显示toast
        toast.style.display = 'block';
        
        // 3秒后隐藏
        setTimeout(function() {
            toast.style.display = 'none';
        }, 3000);
    }

    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // 表单提交加载状态
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
            }
        });
    });
});
