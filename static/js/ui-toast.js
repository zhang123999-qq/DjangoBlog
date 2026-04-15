/**
 * 轻量级 Toast 组件
 * 用法：window.UIToast.show('文本', 'success'|'error'|'info', 2200)
 */
(function (global) {
  'use strict';

  const TYPE_CLASS = {
    success: 'bg-success text-white',
    error: 'bg-danger text-white',
    info: 'bg-dark text-white',
  };

  function ensureContainer() {
    let container = document.getElementById('ui-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ui-toast-container';
      container.style.position = 'fixed';
      container.style.top = '16px';
      container.style.right = '16px';
      container.style.zIndex = '9999';
      container.style.display = 'flex';
      container.style.flexDirection = 'column';
      container.style.gap = '8px';
      container.style.maxWidth = '360px';
      document.body.appendChild(container);
    }
    return container;
  }

  function show(message, type = 'info', timeout = 2200) {
    const container = ensureContainer();
    const toast = document.createElement('div');

    toast.className = `shadow rounded px-3 py-2 small ${TYPE_CLASS[type] || TYPE_CLASS.info}`;
    toast.textContent = message || '操作完成';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-4px)';
    toast.style.transition = 'all .18s ease';

    container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-4px)';
      setTimeout(() => toast.remove(), 180);
    }, timeout);
  }

  global.UIToast = { show };
})(window);
