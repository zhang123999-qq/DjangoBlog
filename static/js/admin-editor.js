/**
 * Django Admin TinyMCE 编辑器初始化
 */
(function() {
    'use strict';
    
    // 等待 DOM 加载完成
    document.addEventListener('DOMContentLoaded', function() {
        initTinyMCE();
    });
    
    // 如果 DOM 已加载完成，立即初始化
    if (document.readyState !== 'loading') {
        initTinyMCE();
    }
    
    function initTinyMCE() {
        // 检查 TinyMCE 是否加载
        if (typeof tinymce === 'undefined') {
            console.warn('TinyMCE not loaded');
            return;
        }
        
        // 查找所有带有 data-editor="tinymce" 的 textarea
        const textareas = document.querySelectorAll('textarea[data-editor="tinymce"]');
        
        textareas.forEach(function(textarea) {
            // 如果已经初始化，跳过
            if (tinymce.get(textarea.id)) {
                return;
            }
            
            // 初始化 TinyMCE
            tinymce.init({
                target: textarea,
                height: 500,
                menubar: true,
                plugins: [
                    'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                    'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                    'insertdatetime', 'media', 'table', 'help', 'wordcount', 'codesample'
                ],
                toolbar: 'undo redo | blocks | formatselect | ' +
                         'bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | ' +
                         'bullist numlist outdent indent | link image media table | ' +
                         'codesample | removeformat code fullscreen help',
                toolbar_mode: 'sliding',
                promotion: false,
                branding: false,
                resize: true,
                statusbar: true,
                elementpath: false,
                paste_data_images: true,
                automatic_uploads: true,
                images_upload_url: '/api/upload/image/',
                images_upload_credentials: true,
                relative_urls: false,
                remove_script_host: false,
                convert_urls: true,
                content_style: `
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        font-size: 15px;
                        line-height: 1.6;
                        color: #333;
                        max-width: 100%;
                        padding: 10px;
                    }
                    pre { 
                        background: #f5f5f5; 
                        padding: 15px; 
                        border-radius: 5px;
                        overflow-x: auto;
                    }
                    code {
                        font-family: 'Fira Code', Monaco, Consolas, monospace;
                        font-size: 14px;
                        background: #f5f5f5;
                        padding: 2px 6px;
                        border-radius: 3px;
                    }
                    pre code {
                        background: none;
                        padding: 0;
                    }
                    img { max-width: 100%; height: auto; }
                    blockquote { 
                        border-left: 4px solid #4f46e5; 
                        padding-left: 16px; 
                        margin-left: 0;
                        color: #666;
                    }
                    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
                    table td, table th { border: 1px solid #e5e7eb; padding: 10px; }
                    table th { background-color: #f9fafb; }
                    h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; }
                    p { margin-bottom: 1em; }
                `,
                setup: function(editor) {
                    // 快捷键保存
                    editor.addShortcut('ctrl+s', '保存', function() {
                        const form = editor.formElement;
                        if (form) {
                            // 触发表单提交
                            const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
                            if (submitBtn) {
                                submitBtn.click();
                            }
                        }
                    });
                    
                    // 编辑器就绪
                    editor.on('init', function() {
                        console.log('TinyMCE initialized for:', textarea.id);
                    });
                }
            });
        });
    }
    
    // 为 Django admin 的添加/修改页面提供重新初始化功能
    window.initAdminTinyMCE = initTinyMCE;
})();
