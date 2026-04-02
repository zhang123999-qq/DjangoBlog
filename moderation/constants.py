"""
审核模块共享常量

提取公共的违规类型映射、结论类型映射、解析函数，
避免 baidu_moderation.py 和 ai_service.py 重复定义。
"""

# ============================================================
# 百度审核结论类型
# ============================================================
CONCLUSION_TYPE = {
    1: '合规',
    2: '疑似',
    3: '不合规',
}

# ============================================================
# 违规类型映射 — 完整版 (baidu_moderation.py 使用)
# ============================================================
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

# ============================================================
# 违规类型映射 — 简化版 (ai_service.py 使用)
# ============================================================
VIOLATION_TYPES_SIMPLE = {
    1: '色情',
    2: '暴恐',
    3: '政治敏感',
    4: '恶意推广',
    5: '低俗辱骂',
    6: '低质灌水',
}

# ============================================================
# 解析函数
# ============================================================

def parse_baidu_violation_data(data):
    """解析百度 API 返回的违规数据

    Args:
        data: 百度 API 返回的 data 列表

    Returns:
        list: 违规详情列表，每项包含 type/msg/_probability/confidence
    """
    if not data or not isinstance(data, list):
        return []

    violations = []
    for item in data:
        if not isinstance(item, dict):
            continue
        raw_type = item.get('type', -1)
        violation_type = raw_type if isinstance(raw_type, int) else -1
        probability = item.get('probability', 0)
        violation = {
            'type': VIOLATION_TYPES.get(violation_type, f'类型{violation_type}'),
            'msg': item.get('msg', ''),
            'probability': probability,
            'confidence': f'{probability * 100:.1f}%',
        }
        violations.append(violation)

    return violations


def parse_baidu_violation_data_simple(data):
    """解析百度 API 违规数据 — 简化版（ai_service.py 用）

    Args:
        data: 百度 API 返回的 data 列表

    Returns:
        list: 简化的违规详情列表，包含 type/msg/probability/hits
    """
    if not data or not isinstance(data, list):
        return []

    violations = []
    for item in data:
        if not isinstance(item, dict):
            continue
        raw_type = item.get('type', -1)
        violation_type = raw_type if isinstance(raw_type, int) else -1
        violation = {
            'type': VIOLATION_TYPES_SIMPLE.get(violation_type, '其他'),
            'msg': item.get('msg', ''),
            'probability': item.get('probability', 0),
            'hits': item.get('hits', []),
        }
        violations.append(violation)

    return violations
