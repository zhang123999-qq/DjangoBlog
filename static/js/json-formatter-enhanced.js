// JSON 格式化工具 - 外部脚本
(function() {
    'use strict';
    
    let inputEditor, outputEditor;

    function mountToast(message, type) {
        type = type || 'success';
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white border-0 position-fixed ' + 
            (type === 'success' ? 'bg-success' : 'bg-danger');
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        
        const toastBody = document.createElement('div');
        toastBody.className = 'd-flex';
        
        const bodyContent = document.createElement('div');
        bodyContent.className = 'toast-body';
        const icon = document.createElement('i');
        icon.className = 'bi ' + (type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle') + ' me-2';
        bodyContent.appendChild(icon);
        bodyContent.appendChild(document.createTextNode(message));
        
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close btn-close-white me-2 m-auto';
        closeBtn.setAttribute('data-bs-dismiss', 'toast');
        
        toastBody.appendChild(bodyContent);
        toastBody.appendChild(closeBtn);
        toast.appendChild(toastBody);
        
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: 2600 });
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', function() { toast.remove(); });
    }

    function formatJSON() {
        var input = inputEditor.getValue();
        var indent = document.getElementById('indent-select').value;
        var sortKeys = document.getElementById('sort-keys').checked;
        
        try {
            var data = JSON.parse(input || '{}');
            var indentStr = indent === 'tab' ? '\t' : parseInt(indent, 10);
            var value;
            if (sortKeys && data && typeof data === 'object' && !Array.isArray(data)) {
                value = JSON.stringify(
                    Object.keys(data).sort().reduce(function(o, k) { o[k] = data[k]; return o; }, {}),
                    null, indentStr
                );
            } else {
                value = JSON.stringify(data, null, indentStr);
            }
            outputEditor.setValue(value);
        } catch (e) {
            mountToast(e.message || 'JSON 格式错误', 'error');
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        MonacoEditor.load().then(function() {
            inputEditor = MonacoEditor.create('input-editor', {
                language: 'json',
                value: '',
                minimap: { enabled: false }
            });
            outputEditor = MonacoEditor.create('output-editor', {
                language: 'json',
                value: '',
                readOnly: true,
                minimap: { enabled: false }
            });
        });
    });

    // 暴露全局函数供 onclick 使用
    window.formatJSON = formatJSON;
})();
