/**
 * 工具搜索功能
 */
(function() {
    'use strict';
    
    function initToolSearch() {
        const searchInput = document.getElementById('tool-search');
        const clearBtn = document.getElementById('clear-search');
        const searchHint = document.getElementById('search-hint');
        const resultCount = document.getElementById('search-result-count');
        const noResults = document.getElementById('no-results');
        const categoryNav = document.getElementById('category-nav');
        const statsSection = document.getElementById('stats-section');
        const categorySections = document.querySelectorAll('.category-section');
        const toolCards = document.querySelectorAll('.tool-card');

        if (!searchInput) return;

        searchInput.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            if (query === '') {
                showAll();
                return;
            }
            performSearch(query);
        });

        clearBtn.addEventListener('click', function() {
            searchInput.value = '';
            showAll();
            searchInput.focus();
        });

        function performSearch(query) {
            let matchCount = 0;

            toolCards.forEach(card => {
                const name = (card.dataset.name || '').toLowerCase();
                const desc = (card.dataset.desc || '').toLowerCase();

                if (name.includes(query) || desc.includes(query)) {
                    card.classList.remove('hidden');
                    matchCount++;
                    highlightText(card, query);
                } else {
                    card.classList.add('hidden');
                    removeHighlight(card);
                }
            });

            categorySections.forEach(section => {
                const visibleCards = section.querySelectorAll('.tool-card:not(.hidden)');
                if (visibleCards.length > 0) {
                    section.classList.remove('hidden');
                    const countEl = section.querySelector('.category-count');
                    if (countEl) countEl.textContent = visibleCards.length + ' 个工具';
                } else {
                    section.classList.add('hidden');
                }
            });

            clearBtn.style.display = query ? 'block' : 'none';
            searchHint.style.display = query ? 'block' : 'none';
            resultCount.textContent = matchCount;
            noResults.style.display = matchCount === 0 ? 'block' : 'none';
            categoryNav.style.display = query ? 'none' : 'flex';
            if (statsSection) statsSection.style.display = query ? 'none' : 'flex';
        }

        function showAll() {
            toolCards.forEach(card => {
                card.classList.remove('hidden');
                removeHighlight(card);
            });

            categorySections.forEach(section => {
                section.classList.remove('hidden');
                const originalCount = section.querySelectorAll('.tool-card').length;
                const countEl = section.querySelector('.category-count');
                if (countEl) countEl.textContent = originalCount + ' 个工具';
            });

            clearBtn.style.display = 'none';
            searchHint.style.display = 'none';
            noResults.style.display = 'none';
            categoryNav.style.display = 'flex';
            if (statsSection) statsSection.style.display = 'flex';
        }

        function highlightText(card, query) {
            const nameEl = card.querySelector('.tool-name');
            const descEl = card.querySelector('.tool-desc');

            if (nameEl) {
                const originalName = nameEl.textContent;
                nameEl.innerHTML = highlightMatch(originalName, query);
            }
            if (descEl) {
                const originalDesc = descEl.textContent;
                descEl.innerHTML = highlightMatch(originalDesc, query);
            }
        }

        function highlightMatch(text, query) {
            const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
            return text.replace(regex, '<span class="highlight">$1</span>');
        }

        function removeHighlight(card) {
            const nameEl = card.querySelector('.tool-name');
            const descEl = card.querySelector('.tool-desc');
            if (nameEl) nameEl.innerHTML = nameEl.textContent;
            if (descEl) descEl.innerHTML = descEl.textContent;
        }

        function escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey && e.key === 'f') || (e.key === '/' && document.activeElement !== searchInput)) {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }
            if (e.key === 'Escape' && searchInput.value) {
                showAll();
                searchInput.value = '';
                searchInput.blur();
            }
        });
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initToolSearch);
    } else {
        initToolSearch();
    }
})();
