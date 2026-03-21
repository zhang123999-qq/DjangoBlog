"""
百度内容审核服务模块

接入百度内容审核 API，支持文本、图片审核
API 文档: https://cloud.baidu.com/doc/ANTIPORN/s/Nk3h6xb2j
"""

import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# 百度审核结论类型
CONCLUSION_TYPE = {
    1: '合规',
    2: '疑似',
    3: '不合规',
}

# 违规类型
VIOLATION_TYPES = {
    1: '色情',
    2: '性感', 
    3: '暴恐',
    4: '违禁',
    5: '涉政',
    6: '辱骂',
    7: '广告',
    8: '灌水',
    9: '涉黄',
    10: '低俗',
    11: '涉价值观',
    12: '涉疆',
    13: '涉港',
    14: '涉台',
    15: '涉藏',
    16: '宗教',
    17: '迷信',
    18: '违法',
    19: '欺诈',
    20: '交易',
}


def get_baidu_client():
    """
    获取百度内容审核客户端
    
    Returns:
        AipContentCensor | None: 客户端实例，未配置时返回 None
    """
    if not settings.BAIDU_MODERATION_ENABLED:
        return None
    
    try:
        from aip import AipContentCensor
        client = AipContentCensor(
            settings.BAIDU_APP_ID,
            settings.BAIDU_API_KEY,
            settings.BAIDU_SECRET_KEY
        )
        return client
    except ImportError:
        logger.error('baidu-aip 未安装，请运行: pip install baidu-aip')
        return None
    except Exception as e:
        logger.error(f'初始化百度内容审核客户端失败: {e}')
        return None


def moderate_text(content):
    """
    文本内容审核
    
    Args:
        content: 要审核的文本内容
    
    Returns:
        tuple: (status, details)
            - status: 'approved' | 'rejected' | 'pending' | 'error'
            - details: 审核详情，包含违规类型、置信度等
    """
    if not content or not content.strip():
        return 'approved', {'message': '内容为空，自动通过'}
    
    # 检查是否启用百度审核
    if not settings.BAIDU_MODERATION_ENABLED:
        logger.debug('百度内容审核未启用，跳过 AI 审核')
        return 'pending', {'message': 'AI审核未启用'}
    
    client = get_baidu_client()
    if not client:
        return 'pending', {'message': 'AI审核服务不可用'}
    
    try:
        # 调用百度文本审核 API
        result = client.textCensorUserDefined(content)
        
        # 解析结果
        conclusion_type = result.get('conclusionType', 2)
        
        if conclusion_type == 1:
            # 合规
            return 'approved', {
                'message': 'AI审核通过',
                'conclusion': CONCLUSION_TYPE.get(conclusion_type, '未知'),
            }
        
        elif conclusion_type == 3:
            # 不合规
            data = result.get('data', [])
            violations = []
            
            for item in data:
                violation_type = item.get('type', 0)
                msg = item.get('msg', '')
                confidence = item.get('probability', 0) * 100
                
                violations.append({
                    'type': VIOLATION_TYPES.get(violation_type, f'类型{violation_type}'),
                    'message': msg,
                    'confidence': f'{confidence:.1f}%',
                })
            
            return 'rejected', {
                'message': 'AI识别违规内容',
                'conclusion': CONCLUSION_TYPE.get(conclusion_type, '不合规'),
                'violations': violations,
            }
        
        elif conclusion_type == 2:
            # 疑似，需要人工审核
            data = result.get('data', [])
            suspicions = []
            
            for item in data:
                suspicion_type = item.get('type', 0)
                msg = item.get('msg', '')
                confidence = item.get('probability', 0) * 100
                
                suspicions.append({
                    'type': VIOLATION_TYPES.get(suspicion_type, f'类型{suspicion_type}'),
                    'message': msg,
                    'confidence': f'{confidence:.1f}%',
                })
            
            return 'pending', {
                'message': 'AI识别疑似违规，需人工审核',
                'conclusion': CONCLUSION_TYPE.get(conclusion_type, '疑似'),
                'suspicions': suspicions,
            }
        
        else:
            # 未知结论，保守处理
            logger.warning(f'百度审核返回未知结论类型: {conclusion_type}')
            return 'pending', {
                'message': 'AI审核结果不确定',
                'raw_result': result,
            }
    
    except Exception as e:
        logger.error(f'百度文本审核失败: {e}')
        return 'error', {
            'message': f'AI审核服务异常: {str(e)}',
        }


def moderate_image(image_data):
    """
    图片内容审核
    
    Args:
        image_data: 图片二进制数据或文件路径
    
    Returns:
        tuple: (status, details)
    """
    # 检查是否启用百度审核
    if not settings.BAIDU_MODERATION_ENABLED:
        return 'pending', {'message': 'AI审核未启用'}
    
    client = get_baidu_client()
    if not client:
        return 'pending', {'message': 'AI审核服务不可用'}
    
    try:
        # 读取图片数据
        if isinstance(image_data, str):
            # 文件路径
            with open(image_data, 'rb') as f:
                image_data = f.read()
        
        # 调用百度图片审核 API
        result = client.imageCensorUserDefined(image_data)
        
        conclusion_type = result.get('conclusionType', 2)
        
        if conclusion_type == 1:
            return 'approved', {
                'message': '图片AI审核通过',
                'conclusion': CONCLUSION_TYPE.get(conclusion_type, '合规'),
            }
        
        elif conclusion_type == 3:
            data = result.get('data', [])
            violations = []
            
            for item in data:
                violation_type = item.get('type', 0)
                msg = item.get('msg', '')
                confidence = item.get('probability', 0) * 100
                
                violations.append({
                    'type': VIOLATION_TYPES.get(violation_type, f'类型{violation_type}'),
                    'message': msg,
                    'confidence': f'{confidence:.1f}%',
                })
            
            return 'rejected', {
                'message': '图片AI识别违规',
                'conclusion': CONCLUSION_TYPE.get(conclusion_type, '不合规'),
                'violations': violations,
            }
        
        elif conclusion_type == 2:
            return 'pending', {
                'message': '图片AI识别疑似违规',
                'conclusion': CONCLUSION_TYPE.get(conclusion_type, '疑似'),
            }
        
        else:
            return 'pending', {
                'message': '图片AI审核结果不确定',
                'raw_result': result,
            }
    
    except Exception as e:
        logger.error(f'百度图片审核失败: {e}')
        return 'error', {
            'message': f'图片AI审核服务异常: {str(e)}',
        }


def smart_moderate(content, check_sensitive=True):
    """
    智能审核：敏感词 + AI 双重检测
    
    Args:
        content: 要审核的文本内容
        check_sensitive: 是否进行敏感词检测
    
    Returns:
        tuple: (status, details)
    """
    from .utils import check_sensitive_content
    
    details = {
        'sensitive_check': None,
        'ai_check': None,
    }
    
    # 1. 敏感词快速检测（本地，速度快）
    if check_sensitive:
        has_sensitive, hit_words = check_sensitive_content(content)
        details['sensitive_check'] = {
            'has_sensitive': has_sensitive,
            'hit_words': hit_words,
        }
        
        if has_sensitive:
            return 'pending', {
                'message': f'命中敏感词: {", ".join(hit_words)}',
                'details': details,
            }
    
    # 2. AI 语义审核
    ai_status, ai_details = moderate_text(content)
    details['ai_check'] = ai_details
    
    return ai_status, details


def get_moderation_summary(status, details):
    """
    生成审核摘要（用于存储到 review_note 字段）
    
    Args:
        status: 审核状态
        details: 审核详情
    
    Returns:
        str: 审核摘要
    """
    if status == 'approved':
        return 'AI审核通过'
    
    elif status == 'rejected':
        violations = details.get('violations', [])
        if violations:
            types = [v['type'] for v in violations]
            return f"AI识别违规: {', '.join(types)}"
        return 'AI识别违规内容'
    
    elif status == 'pending':
        reasons = []
        
        # 敏感词
        sensitive = details.get('details', {}).get('sensitive_check', {})
        if sensitive.get('has_sensitive'):
            words = sensitive.get('hit_words', [])
            reasons.append(f"敏感词: {', '.join(words[:3])}")
        
        # AI 疑似
        ai = details.get('details', {}).get('ai_check', {})
        if ai.get('suspicions'):
            types = [s['type'] for s in ai['suspicions'][:3]]
            reasons.append(f"AI疑似: {', '.join(types)}")
        
        if reasons:
            return ' | '.join(reasons)
        return '需人工审核'
    
    elif status == 'error':
        return f"AI审核异常: {details.get('message', '未知错误')}"
    
    return '未知状态'
