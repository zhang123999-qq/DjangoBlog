/**
 * 公安联网备案号自动生成
 */
(function() {
    'use strict';
    
    function initGonganBeian() {
        const gonganField = document.getElementById('id_site_gongan_beian');
        if (!gonganField) return;
        if (document.getElementById('btn-fill-gongan')) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'admin-inline-action';
        
        const button = document.createElement('button');
        button.type = 'button';
        button.id = 'btn-fill-gongan';
        button.className = 'admin-inline-button';
        button.textContent = '补全公安备案格式';
        
        const hint = document.createElement('span');
        hint.id = 'gongan-hint';
        hint.className = 'admin-inline-hint';
        hint.hidden = true;
        hint.textContent = '请替换为真实备案编号后保存';
        
        wrapper.appendChild(button);
        wrapper.appendChild(hint);
        gonganField.parentNode.appendChild(wrapper);

        button.addEventListener('click', function() {
            gonganField.value = '京公网安备 11010502030001号';
            gonganField.focus();
            gonganField.select();
            hint.hidden = false;
        });
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGonganBeian);
    } else {
        initGonganBeian();
    }
})();
