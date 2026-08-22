"""
核心模块性能基准测试

覆盖：
- 敏感词检测 (Aho-Corasick)
- 浏览量计数器
- 缓存操作
- 数据库查询优化
"""

import time
from typing import List

import pytest
from django.test import override_settings


# ============================================================
# 敏感词检测基准测试
# ============================================================

@pytest.mark.django_db
class TestSensitiveWordBenchmark:
    """敏感词检测性能基准"""

    @pytest.fixture(autouse=True)
    def setup(self, django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            from moderation.models import SensitiveWord
            # 创建测试敏感词（1000 个）
            words = [f"敏感词{i}" for i in range(1000)]
            SensitiveWord.objects.bulk_create(
                [SensitiveWord(word=w, is_active=True, category="test") for w in words],
                ignore_conflicts=True
            )
        yield

    def test_aho_corasick_short_text(self, benchmark):
        """短文本检测基准 (< 100 字符)"""
        from moderation.utils import check_sensitive_content

        text = "这是一个包含敏感词123和敏感词456的测试文本"

        def run():
            return check_sensitive_content(text)

        result = benchmark(run)
        assert result[0] is True  # 应检测到敏感词

    def test_aho_corasick_medium_text(self, benchmark):
        """中等文本检测基准 (100-1000 字符)"""
        from moderation.utils import check_sensitive_content

        text = "这是一个测试文本 " + "敏感词123 " * 50

        def run():
            return check_sensitive_content(text)

        result = benchmark(run)
        assert result[0] is True

    def test_aho_corasick_long_text(self, benchmark):
        """长文本检测基准 (> 1000 字符)"""
        from moderation.utils import check_sensitive_content

        text = "这是一个长测试文本 " + "敏感词456 " * 200

        def run():
            return check_sensitive_content(text)

        result = benchmark(run)
        assert result[0] is True

    def test_aho_corasick_clean_text(self, benchmark):
        """无敏感词文本基准"""
        from moderation.utils import check_sensitive_content

        text = "这是一个完全正常的文本，不包含任何敏感内容。" * 50

        def run():
            return check_sensitive_content(text)

        result = benchmark(run)
        assert result[0] is False

    def test_sensitive_word_cache_rebuild(self, benchmark):
        """敏感词缓存重建基准"""
        from moderation.utils import get_sensitive_words, _build_automaton
        from django.core.cache import cache

        def run():
            cache.delete("sensitive_words_automaton")
            cache.delete("sensitive_words_version")
            words = get_sensitive_words()
            _build_automaton(words)

        benchmark(run)


# ============================================================
# 浏览量计数器基准测试
# ============================================================

@pytest.mark.django_db
class TestViewsCounterBenchmark:
    """浏览量计数器性能基准"""

    @pytest.fixture(autouse=True)
    def setup(self, django_db_blocker):
        with django_db_blocker.unblock():
            from apps.blog.models import Post, Category
            from apps.accounts.models import User
            # 创建测试数据
            self.user = User.objects.create_user(username="bench_user", password="pass")
            self.category = Category.objects.create(name="测试", slug="test")
            self.posts = Post.objects.bulk_create([
                Post(
                    title=f"文章{i}",
                    slug=f"post-{i}",
                    content="内容" * 100,
                    author=self.user,
                    category=self.category,
                    status="published"
                )
                for i in range(100)
            ])

    def test_increment_single(self, benchmark):
        """单次浏览量记录基准"""
        from apps.core.views_counter import ViewsCounter

        def run():
            ViewsCounter.increment('post', self.posts[0].id, None)

        benchmark(run)

    def test_increment_batch(self, benchmark):
        """批量浏览量记录基准 (100 次)"""
        from apps.core.views_counter import ViewsCounter

        def run():
            for i in range(100):
                ViewsCounter.increment('post', self.posts[i % 100].id, None)

        benchmark(run)

    def test_get_views_cached(self, benchmark):
        """缓存命中获取浏览量基准"""
        from apps.core.views_counter import ViewsCounter

        # 预热缓存
        for post in self.posts[:10]:
            ViewsCounter.increment('post', post.id, None)

        def run():
            for post in self.posts[:10]:
                ViewsCounter.get_views('post', post.id)

        benchmark(run)

    def test_sync_to_db(self, benchmark):
        """同步到数据库基准"""
        from apps.core.views_counter import ViewsCounter

        # 预热：产生一些浏览量
        for i in range(50):
            ViewsCounter.increment('post', self.posts[i % 100].id, None)

        def run():
            ViewsCounter.sync_to_db('post')

        benchmark(run)


# ============================================================
# 缓存操作基准测试
# ============================================================

class TestCacheBenchmark:
    """缓存操作性能基准"""

    def test_cache_set_get(self, benchmark):
        """缓存读写基准"""
        from django.core.cache import cache

        def run():
            for i in range(1000):
                cache.set(f"bench_key_{i}", f"value_{i}", 300)
            for i in range(1000):
                cache.get(f"bench_key_{i}")

        benchmark(run)

    def test_cache_pipeline(self, benchmark):
        """管道操作基准 (Redis)"""
        from django.core.cache import cache

        def run():
            pipe = cache.client.get_client().pipeline()
            for i in range(1000):
                pipe.set(f"pipe_key_{i}", f"value_{i}")
            pipe.execute()

        benchmark(run)


# ============================================================
# 数据库查询基准测试
# ============================================================

@pytest.mark.django_db
class TestDatabaseQueryBenchmark:
    """数据库查询性能基准"""

    @pytest.fixture(autouse=True)
    def setup(self, django_db_blocker):
        with django_db_blocker.unblock():
            from apps.blog.models import Post, Category, Tag
            from apps.accounts.models import User

            self.user = User.objects.create_user(username="db_bench", password="pass")
            self.category = Category.objects.create(name="基准分类", slug="bench-cat")
            self.tags = Tag.objects.bulk_create([
                Tag(name=f"标签{i}", slug=f"tag-{i}") for i in range(20)
            ])

            self.posts = Post.objects.bulk_create([
                Post(
                    title=f"基准文章{i}",
                    slug=f"bench-post-{i}",
                    content="内容" * 200,
                    author=self.user,
                    category=self.category,
                    status="published"
                )
                for i in range(500)
            ])

            # 添加标签
            for post in self.posts:
                post.tags.set(self.tags[:5])

    def test_post_list_with_select_related(self, benchmark):
        """select_related 优化查询基准"""
        from apps.blog.models import Post

        def run():
            list(Post.objects.select_related('author', 'category')
                 .filter(status="published")[:50])

        benchmark(run)

    def test_post_list_with_prefetch_related(self, benchmark):
        """prefetch_related 优化查询基准"""
        from apps.blog.models import Post

        def run():
            list(Post.objects.prefetch_related('tags')
                 .filter(status="published")[:50])

        benchmark(run)

    def test_post_list_optimized(self, benchmark):
        """组合优化查询基准"""
        from apps.blog.models import Post

        def run():
            list(Post.objects.select_related('author', 'category')
                 .prefetch_related('tags')
                 .filter(status="published")
                 .only('title', 'slug', 'author__username', 'category__name')[:50])

        benchmark(run)

    def test_post_count_by_category(self, benchmark):
        """分组统计查询基准"""
        from django.db.models import Count
        from apps.blog.models import Post, Category

        def run():
            list(Category.objects.annotate(post_count=Count('posts'))
                 .filter(posts__status="published")
                 .values('name', 'post_count'))

        benchmark(run)


# ============================================================
# 运行配置
# ============================================================

# pytest.ini 额外配置（需添加到项目 pytest.ini）
"""
[tool.pytest.ini_options]
benchmark_min_rounds = 5
benchmark_max_time = 10.0
benchmark_timer = time.perf_counter
benchmark_warmup = True
benchmark_warmup_iterations = 2
"""