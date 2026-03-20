/**
 * DjangoBlog 科技风格特效脚本
 * Tech Theme Effects
 * @version 1.0.0
 * @author DjangoBlog Team
 * @license MIT
 */

'use strict';

/**
 * 配置对象
 * @const {Object}
 */
const CONFIG = {
    /** @type {boolean} 调试模式 */
    DEBUG: false,
    /** @type {number} 动画帧率 */
    FPS: 60,
    /** @type {number} 粒子最大数量 */
    MAX_PARTICLES: 50
};

// ============================================
// 1. 导航栏滚动效果
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar-tech');
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
});

// ============================================
// 2. 粒子背景效果（性能优化版）
// ============================================

class ParticleBackground {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        // 检测是否为触摸设备（移动端减少粒子）
        this.isTouchDevice = window.matchMedia('(pointer: coarse)').matches;
        // 检测是否偏好减少动画
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        if (this.prefersReducedMotion) {
            return; // 用户偏好减少动画，不初始化
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.animationId = null;
        this.lastTime = 0;
        this.frameInterval = this.isTouchDevice ? 33 : 16; // 移动端 30fps，桌面 60fps
        
        this.init();
    }
    
    init() {
        this.resize();
        this.createParticles();
        this.animate();
        
        window.addEventListener('resize', debounce(() => this.resize(), 250));
        
        // 页面不可见时暂停动画（性能优化）
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pause();
            } else {
                this.resume();
            }
        });
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createParticles() {
        // 根据设备性能调整粒子数量
        const baseCount = this.isTouchDevice ? 30000 : 15000;
        const particleCount = Math.floor((this.canvas.width * this.canvas.height) / baseCount);
        const maxParticles = this.isTouchDevice ? 20 : 50; // 限制最大数量
        const finalCount = Math.min(particleCount, maxParticles);
        
        for (let i = 0; i < finalCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }
    
    animate(currentTime = 0) {
        // 节流控制帧率
        const deltaTime = currentTime - this.lastTime;
        if (deltaTime < this.frameInterval) {
            this.animationId = requestAnimationFrame((time) => this.animate(time));
            return;
        }
        this.lastTime = currentTime - (deltaTime % this.frameInterval);
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新和绘制粒子
        this.particles.forEach((particle, i) => {
            // 更新位置
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // 边界检测
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
            
            // 绘制粒子
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity})`;
            this.ctx.fill();
            
            // 绘制连线（移动端跳过以提升性能）
            if (!this.isTouchDevice) {
                for (let j = i + 1; j < this.particles.length; j++) {
                    const dx = this.particles[j].x - particle.x;
                    const dy = this.particles[j].y - particle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < 150) {
                        this.ctx.beginPath();
                        this.ctx.moveTo(particle.x, particle.y);
                        this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                        this.ctx.strokeStyle = `rgba(0, 212, 255, ${0.1 * (1 - distance / 150)})`;
                        this.ctx.stroke();
                    }
                }
            }
        });
        
        this.animationId = requestAnimationFrame((time) => this.animate(time));
    }
    
    pause() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    resume() {
        if (!this.animationId) {
            this.animate();
        }
    }
}

// ============================================
// 3. 打字机效果
// ============================================

class TypeWriter {
    constructor(element, text, speed = 100) {
        this.element = element;
        this.text = text;
        this.speed = speed;
        this.index = 0;
        this.isTyping = false;
    }
    
    type() {
        if (this.isTyping) return;
        this.isTyping = true;
        
        const typeChar = () => {
            if (this.index < this.text.length) {
                this.element.textContent += this.text.charAt(this.index);
                this.index++;
                setTimeout(typeChar, this.speed);
            } else {
                this.isTyping = false;
            }
        };
        
        typeChar();
    }
    
    reset() {
        this.index = 0;
        this.element.textContent = '';
        this.isTyping = false;
    }
}

// ============================================
// 4. 数字滚动动画
// ============================================

function animateNumber(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target.toLocaleString();
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current).toLocaleString();
        }
    }, 16);
}

// ============================================
// 5. 渐入动画
// ============================================

function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(el => observer.observe(el));
}

// ============================================
// 6. 工具卡片悬停效果
// ============================================

function initToolCards() {
    const toolCards = document.querySelectorAll('.tool-card-tech');
    
    toolCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// ============================================
// 7. 搜索框焦点效果
// ============================================

function initSearchBox() {
    const searchInputs = document.querySelectorAll('.search-box input');
    
    searchInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
}

// ============================================
// 8. 代码高亮（简单版）
// ============================================

function highlightCode() {
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(block => {
        // 简单的语法高亮
        let html = block.innerHTML;
        
        // 关键字
        html = html.replace(/\b(function|return|var|let|const|if|else|for|while|class|import|from)\b/g, 
            '<span style="color: #f472b6">$1</span>');
        
        // 字符串
        html = html.replace(/(['"`])(.*?)\1/g, 
            '<span style="color: #10b981">$1$2$1</span>');
        
        // 注释
        html = html.replace(/(\/\/.*$|\/\*[\s\S]*?\*\/)/gm, 
            '<span style="color: #6b7280">$1</span>');
        
        block.innerHTML = html;
    });
}

// ============================================
// 9. 复制代码功能
// ============================================

function initCopyCode() {
    const codeBlocks = document.querySelectorAll('pre');
    
    codeBlocks.forEach(block => {
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-tech-ghost copy-btn';
        button.innerHTML = '<i class="bi bi-clipboard"></i>';
        button.style.cssText = 'position: absolute; top: 10px; right: 10px; opacity: 0; transition: opacity 0.3s;';
        
        block.style.position = 'relative';
        block.appendChild(button);
        
        block.addEventListener('mouseenter', () => button.style.opacity = '1');
        block.addEventListener('mouseleave', () => button.style.opacity = '0');
        
        button.addEventListener('click', async () => {
            const code = block.querySelector('code').textContent;
            await navigator.clipboard.writeText(code);
            
            button.innerHTML = '<i class="bi bi-check"></i>';
            button.style.color = '#10b981';
            
            setTimeout(() => {
                button.innerHTML = '<i class="bi bi-clipboard"></i>';
                button.style.color = '';
            }, 2000);
        });
    });
}

// ============================================
// 10. 初始化所有功能
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // 初始化粒子背景（如果存在 canvas）
    // new ParticleBackground('particles');
    
    // 初始化滚动动画
    initScrollAnimations();
    
    // 初始化工具卡片
    initToolCards();
    
    // 初始化搜索框
    initSearchBox();
    
    // 代码高亮
    highlightCode();
    
    // 复制代码功能
    initCopyCode();
    
    // 数字滚动动画
    const statElements = document.querySelectorAll('.stat-value[data-target]');
    statElements.forEach(el => {
        const target = parseInt(el.dataset.target);
        if (target) {
            // 使用 IntersectionObserver 在元素进入视口时开始动画
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animateNumber(el, target);
                        observer.unobserve(el);
                    }
                });
            });
            observer.observe(el);
        }
    });
    
    // 生产环境移除调试日志
    // console.log('[Tech Theme] 科技主题特效已加载');
});

// ============================================
// 11. 工具函数
// ============================================

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 平滑滚动到指定元素
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// 显示 Toast 提示
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed`;
    toast.style.cssText = 'top: 100px; right: 20px; z-index: 9999; min-width: 200px;';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
