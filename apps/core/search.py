"""
全文搜索服务

支持后端：
- Meilisearch（推荐，轻量级）
- Elasticsearch（功能丰富）

配置：
    # settings.py
    SEARCH_BACKEND = 'meilisearch'  # 或 'elasticsearch'
    MEILISEARCH_HOST = 'http://localhost:7700'
    MEILISEARCH_API_KEY = 'your-api-key'
    ELASTICSEARCH_HOST = ['http://localhost:9200']
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)


class SearchBackend(ABC):
    """搜索后端抽象基类"""

    @abstractmethod
    def index_document(self, index: str, doc_id: str, document: Dict) -> bool:
        """索引文档"""

    @abstractmethod
    def delete_document(self, index: str, doc_id: str) -> bool:
        """删除文档"""

    @abstractmethod
    def search(self, index: str, query: str, **kwargs) -> Dict:
        """搜索"""

    @abstractmethod
    def create_index(self, index: str, settings: Optional[Dict] = None) -> bool:
        """创建索引"""

    @abstractmethod
    def delete_index(self, index: str) -> bool:
        """删除索引"""

    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""


class MeilisearchBackend(SearchBackend):
    """Meilisearch 后端"""

    def __init__(self):
        self.host = getattr(settings, "MEILISEARCH_HOST", "http://localhost:7700")
        self.api_key = getattr(settings, "MEILISEARCH_API_KEY", "")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import meilisearch

                self._client = meilisearch.Client(self.host, self.api_key)
            except ImportError:
                logger.warning("meilisearch-python 未安装，请运行: pip install meilisearch")
                return None
        return self._client

    def index_document(self, index: str, doc_id: str, document: Dict) -> bool:
        try:
            if self.client is None:
                return False

            index = self.client.index(index)
            document["id"] = doc_id  # Meilisearch 使用 id 字段
            index.add_documents([document])
            return True
        except Exception as e:
            logger.error(f"Meilisearch 索引文档失败: {e}")
            return False

    def delete_document(self, index: str, doc_id: str) -> bool:
        try:
            if self.client is None:
                return False

            index = self.client.index(index)
            index.delete_document(doc_id)
            return True
        except Exception as e:
            logger.error(f"Meilisearch 删除文档失败: {e}")
            return False

    def search(self, index: str, query: str, **kwargs) -> Dict:
        try:
            if self.client is None:
                return {"hits": [], "total": 0}

            search_index = self.client.index(index)

            # 构建搜索参数
            search_params = {}
            if kwargs.get("filters"):
                search_params["filter"] = kwargs["filters"]
            if kwargs.get("limit"):
                search_params["limit"] = kwargs["limit"]
            if kwargs.get("offset"):
                search_params["offset"] = kwargs["offset"]
            if kwargs.get("sort"):
                search_params["sort"] = kwargs["sort"]

            # 执行搜索
            results = search_index.search(query, search_params)

            return {
                "hits": results.get("hits", []),
                "total": results.get("estimatedTotalHits", 0),
                "processing_time_ms": results.get("processingTimeMs", 0),
            }
        except Exception as e:
            logger.error(f"Meilisearch 搜索失败: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def create_index(self, index: str, settings: Optional[Dict] = None) -> bool:
        try:
            if self.client is None:
                return False

            # Meilisearch 自动创建索引
            if settings:
                search_index = self.client.index(index)
                search_index.update_settings(settings)
            return True
        except Exception as e:
            logger.error(f"Meilisearch 创建索引失败: {e}")
            return False

    def delete_index(self, index: str) -> bool:
        try:
            if self.client is None:
                return False

            self.client.index(index).delete()
            return True
        except Exception as e:
            logger.error(f"Meilisearch 删除索引失败: {e}")
            return False

    def health_check(self) -> bool:
        try:
            if self.client is None:
                return False
            return self.client.is_healthy()
        except Exception:
            return False


class ElasticsearchBackend(SearchBackend):
    """Elasticsearch 后端"""

    def __init__(self):
        self.hosts = getattr(settings, "ELASTICSEARCH_HOST", ["http://localhost:9200"])
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from elasticsearch import Elasticsearch

                self._client = Elasticsearch(self.hosts)
            except ImportError:
                logger.warning("elasticsearch 未安装，请运行: pip install elasticsearch")
                return None
        return self._client

    def index_document(self, index: str, doc_id: str, document: Dict) -> bool:
        try:
            if self.client is None:
                return False

            self.client.index(index=index, id=doc_id, document=document)
            return True
        except Exception as e:
            logger.error(f"Elasticsearch 索引文档失败: {e}")
            return False

    def delete_document(self, index: str, doc_id: str) -> bool:
        try:
            if self.client is None:
                return False

            self.client.delete(index=index, id=doc_id)
            return True
        except Exception as e:
            logger.error(f"Elasticsearch 删除文档失败: {e}")
            return False

    def search(self, index: str, query: str, **kwargs) -> Dict:
        try:
            if self.client is None:
                return {"hits": [], "total": 0}

            # 构建查询
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": kwargs.get("fields", ["*"]),
                        "fuzziness": "AUTO",
                    }
                },
                "from": kwargs.get("offset", 0),
                "size": kwargs.get("limit", 20),
            }

            # 添加过滤器
            if kwargs.get("filters"):
                search_body["query"] = {"bool": {"must": [search_body["query"]], "filter": kwargs["filters"]}}

            # 执行搜索
            response = self.client.search(index=index, body=search_body)

            hits = [{"id": hit["_id"], **hit["_source"], "_score": hit["_score"]} for hit in response["hits"]["hits"]]

            return {
                "hits": hits,
                "total": response["hits"]["total"]["value"],
            }
        except Exception as e:
            logger.error(f"Elasticsearch 搜索失败: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def create_index(self, index: str, settings: Optional[Dict] = None) -> bool:
        try:
            if self.client is None:
                return False

            if not self.client.indices.exists(index=index):
                self.client.indices.create(index=index, body=settings or {})
            return True
        except Exception as e:
            logger.error(f"Elasticsearch 创建索引失败: {e}")
            return False

    def delete_index(self, index: str) -> bool:
        try:
            if self.client is None:
                return False

            self.client.indices.delete(index=index, ignore_unavailable=True)
            return True
        except Exception as e:
            logger.error(f"Elasticsearch 删除索引失败: {e}")
            return False

    def health_check(self) -> bool:
        try:
            if self.client is None:
                return False
            return self.client.ping()
        except Exception:
            return False


class DatabaseSearchBackend(SearchBackend):
    """数据库搜索后端（降级方案）"""

    def index_document(self, index: str, doc_id: str, document: Dict) -> bool:
        # 数据库搜索不需要索引
        return True

    def delete_document(self, index: str, doc_id: str) -> bool:
        return True

    def search(self, index: str, query: str, **kwargs) -> Dict:
        """使用数据库 LIKE 查询"""
        try:
            from django.apps import apps

            model_mapping = {
                "posts": "blog.Post",
                "topics": "forum.Topic",
            }

            model_path = model_mapping.get(index)
            if not model_path:
                return {"hits": [], "total": 0}

            model = apps.get_model(model_path)

            # 构建查询
            search_fields = kwargs.get("fields", ["title", "content"])
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})

            # 执行查询
            queryset = model.objects.filter(q_objects)

            # 添加过滤条件
            if index == "posts":
                queryset = queryset.filter(status="published")
            elif index == "topics":
                queryset = queryset.filter(review_status="approved")

            total = queryset.count()
            limit = kwargs.get("limit", 20)
            offset = kwargs.get("offset", 0)

            results = queryset[offset: offset + limit]

            hits = []
            for obj in results:
                hits.append(
                    {
                        "id": str(obj.id),
                        "title": getattr(obj, "title", ""),
                        "content": getattr(obj, "content", "")[:200] + "...",
                        "created_at": str(getattr(obj, "created_at", "")),
                    }
                )

            return {"hits": hits, "total": total}
        except Exception as e:
            logger.error(f"数据库搜索失败: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def create_index(self, index: str, settings: Optional[Dict] = None) -> bool:
        return True

    def delete_index(self, index: str) -> bool:
        return True

    def health_check(self) -> bool:
        return True


class SearchService:
    """
    搜索服务

    使用方法:
        from apps.core.search import SearchService

        # 索引文章
        SearchService.index_post(post)

        # 搜索文章
        results = SearchService.search_posts('Django')
    """

    _backend: Optional[SearchBackend] = None

    @classmethod
    def get_backend(cls) -> SearchBackend:
        """获取搜索后端"""
        if cls._backend is None:
            backend_name = getattr(settings, "SEARCH_BACKEND", "database")

            backends = {
                "meilisearch": MeilisearchBackend,
                "elasticsearch": ElasticsearchBackend,
                "database": DatabaseSearchBackend,
            }

            backend_class = backends.get(backend_name, DatabaseSearchBackend)
            cls._backend = backend_class()

        return cls._backend

    @classmethod
    def index_post(cls, post) -> bool:
        """索引文章"""
        document = {
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "slug": post.slug,
            "status": post.status,
            "views_count": post.views_count,
            "author": post.author.username if post.author else "",
            "category": post.category.name if post.category else "",
            "tags": [tag.name for tag in post.tags.all()],
            "published_at": str(post.published_at) if post.published_at else "",
            "created_at": str(post.created_at),
        }

        return cls.get_backend().index_document("posts", str(post.id), document)

    @classmethod
    def index_topic(cls, topic) -> bool:
        """索引主题"""
        document = {
            "title": topic.title,
            "content": topic.content,
            "author": topic.author.username if topic.author else "",
            "board": topic.board.name if topic.board else "",
            "views_count": topic.views_count,
            "reply_count": topic.reply_count,
            "is_pinned": topic.is_pinned,
            "created_at": str(topic.created_at),
        }

        return cls.get_backend().index_document("topics", str(topic.id), document)

    @classmethod
    def delete_post(cls, post_id: int) -> bool:
        """删除文章索引"""
        return cls.get_backend().delete_document("posts", str(post_id))

    @classmethod
    def delete_topic(cls, topic_id: int) -> bool:
        """删除主题索引"""
        return cls.get_backend().delete_document("topics", str(topic_id))

    @classmethod
    def search_posts(cls, query: str, **kwargs) -> Dict:
        """
        搜索文章

        Args:
            query: 搜索关键词
            **kwargs: 额外参数
                - limit: 结果数量限制
                - offset: 偏移量
                - filters: 过滤条件
                - fields: 搜索字段

        Returns:
            Dict: 搜索结果
        """
        return cls.get_backend().search("posts", query, **kwargs)

    @classmethod
    def search_topics(cls, query: str, **kwargs) -> Dict:
        """搜索主题"""
        return cls.get_backend().search("topics", query, **kwargs)

    @classmethod
    def global_search(cls, query: str, **kwargs) -> Dict:
        """
        全局搜索（搜索所有索引）

        Args:
            query: 搜索关键词

        Returns:
            Dict: 搜索结果
        """
        limit = kwargs.get("limit", 10)

        posts = cls.search_posts(query, limit=limit)
        topics = cls.search_topics(query, limit=limit)

        return {
            "posts": posts,
            "topics": topics,
            "total": posts.get("total", 0) + topics.get("total", 0),
        }

    @classmethod
    def reindex_all(cls) -> Dict:
        """
        重建所有索引

        Returns:
            Dict: 重建结果
        """
        result = {"posts": 0, "topics": 0, "errors": []}

        # 重建文章索引
        try:
            from apps.blog.models import Post

            for post in Post.objects.filter(status="published"):
                if cls.index_post(post):
                    result["posts"] += 1
        except Exception as e:
            result["errors"].append(f"posts: {str(e)}")

        # 重建主题索引
        try:
            from apps.forum.models import Topic

            for topic in Topic.objects.filter(review_status="approved"):
                if cls.index_topic(topic):
                    result["topics"] += 1
        except Exception as e:
            result["errors"].append(f"topics: {str(e)}")

        return result

    @classmethod
    def health_check(cls) -> bool:
        """健康检查"""
        return cls.get_backend().health_check()


# 搜索信号处理
def setup_search_signals():
    """
    设置搜索信号

    当文章/主题创建或更新时自动索引
    """
    from django.db.models.signals import post_save, post_delete
    from django.dispatch import receiver

    @receiver(post_save, sender="blog.Post", dispatch_uid="search_index_post_on_save")
    def index_post_on_save(sender, instance, **kwargs):
        if instance.status == "published":
            SearchService.index_post(instance)
        else:
            SearchService.delete_post(instance.id)

    @receiver(post_delete, sender="blog.Post", dispatch_uid="search_delete_post_on_delete")
    def delete_post_on_delete(sender, instance, **kwargs):
        SearchService.delete_post(instance.id)

    @receiver(post_save, sender="forum.Topic", dispatch_uid="search_index_topic_on_save")
    def index_topic_on_save(sender, instance, **kwargs):
        if instance.review_status == "approved":
            SearchService.index_topic(instance)
        else:
            SearchService.delete_topic(instance.id)

    @receiver(post_delete, sender="forum.Topic", dispatch_uid="search_delete_topic_on_delete")
    def delete_topic_on_delete(sender, instance, **kwargs):
        SearchService.delete_topic(instance.id)
