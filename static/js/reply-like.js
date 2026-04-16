/**
 * 论坛回复点赞功能
 */
(function() {
    'use strict';
    
    function initReplyLike() {
        document.querySelectorAll('.like-btn').forEach(button => {
            button.addEventListener('click', async function() {
                const replyId = this.dataset.replyId;
                const likeUrl = this.dataset.likeUrl;
                const likeCountElement = this.querySelector('.like-count');
                const likeIconElement = this.querySelector('.like-icon');
                
                if (!replyId || !likeUrl) {
                    console.error('缺少必要的数据属性');
                    return;
                }
                
                try {
                    const response = await fetch(likeUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        credentials: 'same-origin'
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success) {
                            likeCountElement.textContent = data.like_count;
                            if (data.liked) {
                                likeIconElement.textContent = '❤️';
                                this.classList.remove('btn-outline-primary');
                                this.classList.add('btn-primary');
                            } else {
                                likeIconElement.textContent = '🤍';
                                this.classList.remove('btn-primary');
                                this.classList.add('btn-outline-primary');
                            }
                        } else {
                            alert(data.message || '点赞失败');
                        }
                    } else {
                        alert('点赞失败，请重试');
                    }
                } catch (error) {
                    console.error('点赞请求失败:', error);
                    alert('点赞失败，请重试');
                }
            });
        });
    }
    
    function getCsrfToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initReplyLike);
    } else {
        initReplyLike();
    }
})();
