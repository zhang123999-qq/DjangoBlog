/**
 * 验证码刷新功能
 */
(function() {
    'use strict';
    
    function initCaptchaRefresh() {
        var captchaImg = document.querySelector('.captcha-img');
        var refreshBtn = document.getElementById('refresh-captcha');
        
        if (!captchaImg || !refreshBtn) {
            return;
        }
        
        function refreshCaptcha() {
            fetch('/accounts/captcha/refresh/')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        captchaImg.src = 'data:image/png;base64,' + data.image;
                    }
                })
                .catch(function(err) {
                    console.error('刷新验证码失败:', err);
                });
        }
        
        // 点击刷新按钮
        refreshBtn.addEventListener('click', refreshCaptcha);
        
        // 点击图片也可以刷新
        captchaImg.addEventListener('click', refreshCaptcha);
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCaptchaRefresh);
    } else {
        initCaptchaRefresh();
    }
})();
