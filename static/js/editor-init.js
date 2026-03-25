/**
 * 编辑器初始化脚本
 * 包含 Monaco Editor 和 TinyMCE 的初始化配置
 */

// ==================== Monaco Editor ====================

// Monaco Editor 加载器
let monacoLoaded = false;
let monacoLoadPromise = null;

/**
 * 加载 Monaco Editor
 */
function loadMonaco() {
    if (monacoLoaded) {
        return Promise.resolve();
    }
    if (monacoLoadPromise) {
        return monacoLoadPromise;
    }
    
    monacoLoadPromise = new Promise((resolve, reject) => {
        // 动态加载 Monaco Editor
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/loader.js';
        script.onload = () => {
            require.config({ 
                paths: { 
                    'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' 
                }
            });
            require(['vs/editor/editor.main'], () => {
                monacoLoaded = true;
                resolve();
            });
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
    
    return monacoLoadPromise;
}

/**
 * 创建 Monaco Editor 实例
 * @param {string} elementId - 容器元素ID
 * @param {object} options - 配置选项
 */
async function createMonacoEditor(elementId, options = {}) {
    await loadMonaco();
    
    const defaultOptions = {
        language: 'javascript',
        theme: 'vs',
        fontSize: 14,
        lineNumbers: 'on',
        minimap: { enabled: false },
        automaticLayout: true,
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        folding: true,
        tabSize: 4,
        insertSpaces: true,
        renderWhitespace: 'selection',
        scrollbar: {
            vertical: 'auto',
            horizontal: 'auto'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    // 检查是否深色主题
    if (document.documentElement.getAttribute('data-theme') === 'dark') {
        finalOptions.theme = 'vs-dark';
    }
    
    const editor = monaco.editor.create(document.getElementById(elementId), finalOptions);
    
    // 支持主题切换
    const observer = new MutationObserver(() => {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'vs-dark' : 'vs';
        monaco.editor.setTheme(theme);
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    
    return editor;
}

/**
 * 根据文件名获取语言类型
 */
function getLanguageFromFilename(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const languageMap = {
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'py': 'python',
        'rb': 'ruby',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'h': 'c',
        'hpp': 'cpp',
        'cs': 'csharp',
        'go': 'go',
        'rs': 'rust',
        'php': 'php',
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'scss': 'scss',
        'less': 'less',
        'json': 'json',
        'xml': 'xml',
        'yaml': 'yaml',
        'yml': 'yaml',
        'md': 'markdown',
        'sql': 'sql',
        'sh': 'shell',
        'bash': 'shell',
        'vue': 'vue',
        'svelte': 'svelte',
        'dockerfile': 'dockerfile',
        'makefile': 'makefile'
    };
    return languageMap[ext] || 'plaintext';
}

// ==================== TinyMCE Editor ====================

let tinymceLoaded = false;
let tinymceLoadPromise = null;
let uploadClientLoaded = false;
let uploadClientLoadPromise = null;

/**
 * 加载 TinyMCE
 */
function loadTinyMCE() {
    if (tinymceLoaded) {
        return Promise.resolve();
    }
    if (tinymceLoadPromise) {
        return tinymceLoadPromise;
    }
    
    tinymceLoadPromise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/tinymce@7/tinymce.min.js';
        script.onload = () => {
            tinymceLoaded = true;
            resolve();
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
    
    return tinymceLoadPromise;
}

function loadUploadAsyncClient() {
    if (uploadClientLoaded || window.UploadAsyncClient) {
        uploadClientLoaded = true;
        return Promise.resolve();
    }
    if (uploadClientLoadPromise) {
        return uploadClientLoadPromise;
    }

    uploadClientLoadPromise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = '/static/js/upload-async-client.js';
        script.onload = () => {
            uploadClientLoaded = true;
            resolve();
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });

    return uploadClientLoadPromise;
}

/**
 * 创建 TinyMCE 编辑器实例
 * @param {string} elementId - textarea元素ID
 * @param {object} options - 配置选项
 */
async function createTinyMCE(elementId, options = {}) {
    await loadTinyMCE();
    await loadUploadAsyncClient();
    
    const defaultOptions = {
        height: 500,
        menubar: true,
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'help', 'wordcount', 'codesample',
            'emoticons', 'hr', 'pagebreak', 'nonbreaking', 'directionality'
        ],
        toolbar: 'undo redo | formatselect | bold italic underline strikethrough | ' +
                 'alignleft aligncenter alignright alignjustify | ' +
                 'bullist numlist outdent indent | link image media table | ' +
                 'codesample emoticons hr | removeformat code fullscreen help',
        toolbar_mode: 'sliding',
        codesample_languages: [
            { text: 'HTML/XML', value: 'markup' },
            { text: 'JavaScript', value: 'javascript' },
            { text: 'CSS', value: 'css' },
            { text: 'Python', value: 'python' },
            { text: 'Java', value: 'java' },
            { text: 'C', value: 'c' },
            { text: 'C++', value: 'cpp' },
            { text: 'C#', value: 'csharp' },
            { text: 'PHP', value: 'php' },
            { text: 'Ruby', value: 'ruby' },
            { text: 'Go', value: 'go' },
            { text: 'Rust', value: 'rust' },
            { text: 'SQL', value: 'sql' },
            { text: 'Bash', value: 'bash' },
            { text: 'JSON', value: 'json' },
            { text: 'YAML', value: 'yaml' },
            { text: 'Markdown', value: 'markdown' }
        ],
        language: 'zh_CN',
        language_url: 'https://cdn.jsdelivr.net/npm/tinymce-lang@7/langs/zh_CN.min.js',
        promotion: false,
        branding: false,
        resize: true,
        statusbar: true,
        elementpath: false,
        paste_data_images: true,
        automatic_uploads: true,
        images_upload_url: '/api/upload/image/',
        images_upload_credentials: true,
        file_picker_types: 'image media file',
        file_picker_callback: function(callback, value, meta) {
            // 仅处理附件上传，图片仍由 TinyMCE 默认 images_upload_url 处理
            if (meta.filetype !== 'file') {
                return;
            }

            const input = document.createElement('input');
            input.type = 'file';
            input.style.display = 'none';
            document.body.appendChild(input);

            input.onchange = async function() {
                const file = input.files && input.files[0];
                document.body.removeChild(input);
                if (!file) return;

                const activeEditor = window.tinymce && window.tinymce.activeEditor;
                let lastStatus = '';
                try {
                    if (activeEditor) activeEditor.setProgressState(true);

                    const result = await window.UploadAsyncClient.uploadFileWithPolling(file, {
                        timeoutMs: 120000,
                        intervalMs: 1500,
                        maxRetries: 3,
                        onProgress: (data) => {
                            if (!activeEditor || !data || data.status === lastStatus) return;
                            lastStatus = data.status;
                            const statusTextMap = {
                                pending: '文件已上传，等待扫描...',
                                scanning: '文件安全扫描中...',
                                ready: '扫描通过，正在完成上传...',
                            };
                            const text = statusTextMap[data.status];
                            if (text) {
                                activeEditor.notificationManager.open({
                                    text,
                                    type: 'info',
                                    timeout: 1200,
                                });
                            }
                        },
                    });

                    callback(result.location, {
                        text: file.name,
                        title: file.name,
                    });

                    if (activeEditor) {
                        activeEditor.notificationManager.open({
                            text: '附件上传成功',
                            type: 'success',
                            timeout: 1500,
                        });
                    }
                } catch (err) {
                    const msg = (window.UploadAsyncClient && window.UploadAsyncClient.getErrorMessage)
                        ? window.UploadAsyncClient.getErrorMessage(err)
                        : (err && err.message ? err.message : '上传失败');
                    if (activeEditor) {
                        activeEditor.notificationManager.open({
                            text: `附件上传失败：${msg}`,
                            type: 'error',
                            timeout: 3200,
                        });
                    } else {
                        alert(`附件上传失败：${msg}`);
                    }
                } finally {
                    if (activeEditor) activeEditor.setProgressState(false);
                }
            };

            input.click();
        },
        relative_urls: false,
        remove_script_host: false,
        convert_urls: true,
        content_style: `
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                font-size: 16px;
                line-height: 1.8;
                color: #333;
                max-width: 100%;
            }
            pre code {
                font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
                font-size: 14px;
            }
            img { max-width: 100%; height: auto; }
            blockquote { 
                border-left: 4px solid #007bff; 
                padding-left: 16px; 
                margin-left: 0;
                color: #666;
            }
            table { border-collapse: collapse; width: 100%; }
            table td, table th { border: 1px solid #ddd; padding: 8px; }
            table th { background-color: #f5f5f5; }
        `,
        setup: function(editor) {
            // 自定义快捷键
            editor.addShortcut('ctrl+s', '保存', function() {
                const form = editor.formElement;
                if (form) {
                    const saveBtn = form.querySelector('button[type="submit"]');
                    if (saveBtn) {
                        saveBtn.click();
                    }
                }
            });
        }
    };
    
    const finalOptions = { 
        ...defaultOptions, 
        target: document.getElementById(elementId),
        ...options 
    };
    
    const editors = await tinymce.init(finalOptions);
    return editors[0];
}

/**
 * 销毁 TinyMCE 编辑器
 */
function destroyTinyMCE(elementId) {
    if (tinymceLoaded) {
        tinymce.get(elementId)?.destroy();
    }
}

// ==================== 工具函数 ====================

/**
 * 自动检测编辑器类型并初始化
 */
function initEditors() {
    // 初始化 Monaco Editor
    document.querySelectorAll('[data-editor="monaco"]').forEach(el => {
        const id = el.id;
        const language = el.dataset.language || 'javascript';
        const value = el.dataset.value || '';
        const readOnly = el.dataset.readonly === 'true';
        const theme = el.dataset.theme || 'auto';
        
        createMonacoEditor(id, {
            language: language,
            value: value,
            readOnly: readOnly,
            theme: theme === 'dark' ? 'vs-dark' : (theme === 'light' ? 'vs' : 'auto')
        }).then(editor => {
            // 触发自定义事件
            el.dispatchEvent(new CustomEvent('editor:ready', { detail: editor }));
        });
    });
    
    // 初始化 TinyMCE
    document.querySelectorAll('[data-editor="tinymce"]').forEach(el => {
        const id = el.id;
        const height = parseInt(el.dataset.height) || 500;
        const menubar = el.dataset.menubar !== 'false';
        const simple = el.dataset.simple === 'true';
        
        const options = {
            height: height,
            menubar: menubar
        };
        
        if (simple) {
            options.plugins = ['lists', 'link', 'autolink'];
            options.toolbar = 'bold italic | bullist numlist | link | removeformat';
            options.menubar = false;
        }
        
        createTinyMCE(id, options).then(editor => {
            el.dispatchEvent(new CustomEvent('editor:ready', { detail: editor }));
        });
    });
}

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', initEditors);

// 导出函数
window.MonacoEditor = {
    create: createMonacoEditor,
    load: loadMonaco,
    getLanguage: getLanguageFromFilename
};

window.TinyMCEditor = {
    create: createTinyMCE,
    load: loadTinyMCE,
    destroy: destroyTinyMCE
};
