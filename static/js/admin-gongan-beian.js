/**
 * 公安联网备案号自动生成
 */
(function() {
    'use strict';
    
    function initGonganBeian() {
        const gonganField = document.getElementById('id_site_gongan_beian');
        if (!gonganField) return;

        // 创建按钮容器
        const wrapper = document.createElement('div');
        wrapper.style.marginTop = '8px';
        
        const button = document.createElement('button');
        button.type = 'button';
        button.id = 'btn-fill-gongan';
        button.style.cssText = 'background:#3b82f6;color:#fff;border:none;padding:6px 16px;border-radius:4px;cursor:pointer;font-size:13px;';
        button.textContent = '🛡️ 自动生成公安联网备案号格式';
        
        const hint = document.createElement('span');
        hint.id = 'gongan-hint';
        hint.style.cssText = 'margin-left:12px;color:#666;font-size:12px;display:none;';
        hint.textContent = '✅ 请修改数字部分后保存';
        
        wrapper.appendChild(button);
        wrapper.appendChild(hint);
        gonganField.parentNode.appendChild(wrapper);

        button.addEventListener('click', function() {
            gonganField.value = '京公网安备 11010502030001号';
            gonganField.focus();
            gonganField.select();
            hint.style.display = 'inline';
        });
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGonganBeian);
    } else {
        initGonganBeian();
    }
})();
