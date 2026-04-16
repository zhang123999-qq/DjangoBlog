/**
 * 文章编辑器初始化
 */
(function() {
    'use strict';
    
    function initPostEditor() {
        // 检查 TinyMCEditor 是否可用
        if (typeof TinyMCEditor === 'undefined') {
            console.warn('TinyMCEditor 未加载');
            return;
        }
        
        // 初始化 TinyMCE 编辑器
        TinyMCEditor.create('id_content', {
            height: 500,
            menubar: true
        }).then(editor => {
            console.log('TinyMCE 编辑器已初始化');
            
            // 快捷键保存
            editor.on('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    const form = document.getElementById('post-form');
                    if (form) form.submit();
                }
            });
        }).catch(err => {
            console.error('TinyMCE 编辑器初始化失败:', err);
        });
        
        // 表单提交前同步编辑器内容
        const form = document.getElementById('post-form');
        if (form) {
            form.addEventListener('submit', function() {
                if (typeof tinymce !== 'undefined') {
                    const editor = tinymce.get('id_content');
                    if (editor) {
                        editor.save();
                    }
                }
            });
        }
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPostEditor);
    } else {
        initPostEditor();
    }
})();
