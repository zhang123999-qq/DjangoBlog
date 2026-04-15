/* json_formatter_enhanced 专用脚本 */

let inputEditor, outputEditor;

function mountToast(message, type='success') {
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white border-0 position-fixed ${type === 'success' ? 'bg-success' : 'bg-danger'}`;
  toast.style.bottom = '20px';
  toast.style.right = '20px';
  toast.style.zIndex = '9999';
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body"><i class="bi ${type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'} me-2"></i>${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  document.body.appendChild(toast);
  const bsToast = new bootstrap.Toast(toast, { delay: 2600 });
  bsToast.show();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function formatJSON() {
  const input = inputEditor.getValue();
  const indent = document.getElementById('indent-select').value;
  const sortKeys = document.getElementById('sort-keys').checked;

  try {
    const data = JSON.parse(input || '{}');
    const indentStr = indent === 'tab' ? '\t' : parseInt(indent, 10);
    const value = sortKeys && data && typeof data === 'object' && !Array.isArray(data)
      ? JSON.stringify(Object.keys(data).sort().reduce((o, k) => (o[k] = data[k], o), {}), null, indentStr)
      : JSON.stringify(data, null, indentStr);
    outputEditor.setValue(value);
  } catch (e) {
    mountToast(e.message || 'JSON 格式错误', 'error');
  }
}

document.addEventListener('DOMContentLoaded', async function() {
  await MonacoEditor.load();

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

  inputEditor.onDidChangeModelContent(() => {
    const value = inputEditor.getValue();
    document.getElementById('char-count').textContent = value.length;
    document.getElementById('line-count').textContent = value ? value.split('\n').length : 0;
  });

  document.getElementById('format-btn').addEventListener('click', formatJSON);

  document.getElementById('copy-btn').addEventListener('click', async () => {
    await navigator.clipboard.writeText(outputEditor.getValue() || '');
    mountToast('已复制到剪贴板', 'success');
  });

  document.getElementById('minify-btn').addEventListener('click', () => {
    try {
      const data = JSON.parse(inputEditor.getValue() || '{}');
      outputEditor.setValue(JSON.stringify(data));
    } catch (e) {
      mountToast(e.message || 'JSON 格式错误', 'error');
    }
  });

  document.getElementById('clear-btn').addEventListener('click', () => {
    inputEditor.setValue('');
    outputEditor.setValue('');
  });

  document.getElementById('sample-btn').addEventListener('click', () => {
    const sample = {
      name: 'Django Blog',
      version: '2.3.2',
      features: ['博客', '论坛', '工具栏'],
      config: { debug: false, database: 'mysql' }
    };
    inputEditor.setValue(JSON.stringify(sample, null, 2));
  });

  inputEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, formatJSON);
});
