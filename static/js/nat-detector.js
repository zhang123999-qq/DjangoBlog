// NAT 检测工具 - 外部脚本
(function() {
    'use strict';
    
    var localCandidates = [];
    var publicIPs = { v4: null, v6: null };
    var detectionStartTime = null;
    
    var stunServers = [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' }
    ];

    function startDetection() {
        localCandidates = [];
        publicIPs = { v4: null, v6: null };
        detectionStartTime = Date.now();
        
        var detectionStatusDiv = document.getElementById('detection-status');
        var resultDiv = document.getElementById('detection-result');
        
        // 重置检测状态
        var spinner = document.createElement('div');
        spinner.className = 'spinner-border text-primary mb-3';
        spinner.setAttribute('role', 'status');
        var span = document.createElement('span');
        span.className = 'visually-hidden';
        span.textContent = '检测中...';
        spinner.appendChild(span);
        
        detectionStatusDiv.innerHTML = '';
        detectionStatusDiv.appendChild(spinner);
        
        var p1 = document.createElement('p');
        p1.className = 'text-muted mb-0';
        p1.textContent = '正在检测您的网络状态...';
        detectionStatusDiv.appendChild(p1);
        
        var p2 = document.createElement('p');
        p2.className = 'text-muted small mt-2';
        p2.id = 'detection-progress';
        p2.textContent = '初始化 WebRTC...';
        detectionStatusDiv.appendChild(p2);
        
        // ... 后续检测逻辑需在 HTML 中保持内联以访问 WebRTC API
        // 建议：保持当前页面内联，或在完整版本中将检测逻辑分离
    }

    window.startDetection = startDetection;
})();
