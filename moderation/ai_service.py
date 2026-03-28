"""
AI 内容审核服务

支持：
- 百度内容审核 API
- 文本审核
- 图片审核
- 异步处理
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from apps.core.error_codes import ErrorCodes, error_message

logger = logging.getLogger(__name__)


class BaiduModerationService:
    """百度内容审核服务"""

    def __init__(self):
        self.app_id = getattr(settings, 'BAIDU_APP_ID', '')
        self.api_key = getattr(settings, 'BAIDU_API_KEY', '')
        self.secret_key = getattr(settings, 'BAIDU_SECRET_KEY', '')
        self.enabled = getattr(settings, 'BAIDU_MODERATION_ENABLED', False)

        self._client = None

    @property
    def client(self):
        """懒加载百度 AI 客户端"""
        if self._client is None and self.enabled:
            try:
                from aip import AipContentCensor

                self._client = AipContentCensor(self.app_id, self.api_key, self.secret_key)
            except ImportError:
                logger.warning('baidu-aip 未安装，AI 审核功能不可用')
                self.enabled = False
            except Exception:
                logger.exception('初始化百度 AI 客户端失败')
                self.enabled = False

        return self._client

    @staticmethod
    def _service_unavailable_payload() -> List[Dict[str, Any]]:
        """统一错误返回，避免把内部异常直接暴露给前端。"""
        return [{
            'type': 'error',
            'code': ErrorCodes.MODERATION_SERVICE_UNAVAILABLE,
            'msg': error_message(ErrorCodes.MODERATION_SERVICE_UNAVAILABLE),
        }]

    def moderate_text(self, content: str) -> Tuple[str, Optional[List[Dict]]]:
        """文本审核

        Args:
            content: 待审核文本

        Returns:
            tuple: (审核结果, 违规详情)
                - 审核结果: 'approved' / 'rejected' / 'pending' / 'error'
                - 违规详情: 违规项列表，无违规时为 None
        """
        if not self.enabled or not self.client:
            logger.debug('AI 审核未启用，跳过')
            return 'pending', None

        if not content or not content.strip():
            return 'approved', None

        try:
            result = self.client.textCensorUserDefined(content)
            if not isinstance(result, dict):
                logger.warning('AI 文本审核返回格式异常: %r', type(result))
                return 'error', self._service_unavailable_payload()

            # 结论类型: 1=合规, 2=疑似, 3=不合规
            conclusion_type = result.get('conclusionType', 2)

            if conclusion_type == 1:
                return 'approved', None
            if conclusion_type == 3:
                data = result.get('data', [])
                violation_details = self._parse_violation_data(data)
                return 'rejected', violation_details

            # 疑似违规，返回详情供人工判断
            data = result.get('data', [])
            violation_details = self._parse_violation_data(data)
            return 'pending', violation_details

        except Exception:
            logger.exception('AI 文本审核失败')
            return 'error', self._service_unavailable_payload()

    def moderate_image(self, image_path: str) -> Tuple[str, Optional[List[Dict]]]:
        """图片审核

        Args:
            image_path: 图片路径

        Returns:
            tuple: (审核结果, 违规详情)
        """
        if not self.enabled or not self.client:
            return 'pending', None

        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            result = self.client.imageCensorUserDefined(image_data)
            if not isinstance(result, dict):
                logger.warning('AI 图片审核返回格式异常: %r', type(result))
                return 'error', self._service_unavailable_payload()

            conclusion_type = result.get('conclusionType', 2)

            if conclusion_type == 1:
                return 'approved', None
            if conclusion_type == 3:
                data = result.get('data', [])
                violation_details = self._parse_violation_data(data)
                return 'rejected', violation_details

            data = result.get('data', [])
            violation_details = self._parse_violation_data(data)
            return 'pending', violation_details

        except FileNotFoundError:
            logger.error('图片文件不存在: %s', image_path)
            return 'error', [{'type': 'error', 'msg': '图片文件不存在'}]
        except Exception:
            logger.exception('AI 图片审核失败')
            return 'error', self._service_unavailable_payload()

    def moderate_image_url(self, image_url: str) -> Tuple[str, Optional[List[Dict]]]:
        """图片 URL 审核

        Args:
            image_url: 图片 URL

        Returns:
            tuple: (审核结果, 违规详情)
        """
        if not self.enabled or not self.client:
            return 'pending', None

        try:
            result = self.client.imageCensorUserDefined(image_url)
            if not isinstance(result, dict):
                logger.warning('AI 图片 URL 审核返回格式异常: %r', type(result))
                return 'error', self._service_unavailable_payload()

            conclusion_type = result.get('conclusionType', 2)

            if conclusion_type == 1:
                return 'approved', None
            if conclusion_type == 3:
                data = result.get('data', [])
                violation_details = self._parse_violation_data(data)
                return 'rejected', violation_details

            data = result.get('data', [])
            violation_details = self._parse_violation_data(data)
            return 'pending', violation_details

        except Exception:
            logger.exception('AI 图片 URL 审核失败')
            return 'error', self._service_unavailable_payload()

    def _parse_violation_data(self, data: List[Dict]) -> List[Dict]:
        """解析违规数据

        Args:
            data: 百度 API 返回的 data 列表

        Returns:
            list: 简化的违规详情列表
        """
        if not data or not isinstance(data, list):
            return []

        violations = []
        type_map = {
            1: '色情',
            2: '暴恐',
            3: '政治敏感',
            4: '恶意推广',
            5: '低俗辱骂',
            6: '低质灌水',
        }

        for item in data:
            if not isinstance(item, dict):
                continue
            raw_type = item.get('type')
            violation_type = raw_type if isinstance(raw_type, int) else -1
            violation = {
                'type': type_map.get(violation_type, '其他'),
                'msg': item.get('msg', ''),
                'probability': item.get('probability', 0),
                'hits': item.get('hits', []),
            }
            violations.append(violation)

        return violations


class MockModerationService:
    """模拟审核服务（开发/测试环境）"""

    # 模拟违规词
    MOCK_VIOLATION_WORDS = [
        '测试违规词',
        '广告测试',
        '敏感测试',
    ]

    def moderate_text(self, content: str) -> Tuple[str, Optional[List[Dict]]]:
        """模拟文本审核"""
        if not content:
            return 'approved', None

        # 检查模拟违规词
        for word in self.MOCK_VIOLATION_WORDS:
            if word in content:
                return 'rejected', [{
                    'type': '模拟违规',
                    'msg': f'包含模拟违规词: {word}',
                    'probability': 0.95,
                }]

        return 'approved', None

    def moderate_image(self, image_path: str) -> Tuple[str, Optional[List[Dict]]]:
        """模拟图片审核"""
        return 'approved', None

    def moderate_image_url(self, image_url: str) -> Tuple[str, Optional[List[Dict]]]:
        """模拟图片 URL 审核"""
        return 'approved', None


@lru_cache(maxsize=1)
def get_moderation_service():
    """获取审核服务实例（进程级缓存）。

    Returns:
        审核服务实例（百度或模拟）
    """
    if getattr(settings, 'BAIDU_MODERATION_ENABLED', False):
        return BaiduModerationService()
    return MockModerationService()
