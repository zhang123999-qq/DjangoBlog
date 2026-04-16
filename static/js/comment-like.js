/**
 * 评论点赞功能
 */
(function() {
    'use strict';
    
    function initCommentLike() {
        const likeButtons = document.querySelectorAll('.like-btn');
        
        likeButtons.forEach(button => {
            button.addEventListener('click', function() {
                const commentId = this.getAttribute('data-comment-id');
                const likeUrl = this.getAttribute('data-like-url');
                
                if (!commentId || !likeUrl) {
                    console.error('缺少必要的数据属性');
                    return;
                }
                
                // 发送点赞请求
                fetch(likeUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 更新点赞数
                        const likeCountElement = this.querySelector('.like-count');
                        if (likeCountElement) {
                            likeCountElement.textContent = data.like_count;
                        }
                        
                        // 更新按钮状态
                        if (data.liked) {
                            this.classList.remove('btn-outline-primary');
                            this.classList.add('btn-primary');
                        } else {
                            this.classList.remove('btn-primary');
                            this.classList.add('btn-outline-primary');
                        }
                    } else {
                        // 显示错误信息
                        alert(data.message || '点赞失败');
                    }
                })
                .catch(error => {
                    console.error('点赞失败:', error);
                    alert('点赞失败，请稍后重试');
                });
            });
        });
    }
    
    function getCsrfToken() {
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCommentLike);
    } else {
        initCommentLike();
    }
})();
