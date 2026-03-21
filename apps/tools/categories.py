"""
工具分类定义
"""

# 工具分类常量
class ToolCategory:
    ENCRYPT = 'encrypt'           # 加密解密
    ENCODE = 'encode'             # 编码转换
    TEXT = 'text'                 # 文本处理
    GENERATE = 'generate'         # 生成工具
    DATA = 'data'                 # 数据格式
    TIME = 'time'                 # 时间日期
    IMAGE = 'image'               # 图片工具
    NETWORK = 'network'           # 网络工具
    SECURITY = 'security'         # 安全工具
    CALC = 'calc'                 # 计算工具
    FILE = 'file'                 # 文件工具
    OTHER = 'other'               # 其他工具


# 分类配置（名称、图标、颜色、描述）
TOOL_CATEGORIES = {
    ToolCategory.ENCRYPT: {
        'name': '加密解密',
        'icon': 'bi-shield-lock',
        'color': '#e74c3c',
        'description': 'AES、RSA、Base64、哈希等加密解密工具',
    },
    ToolCategory.ENCODE: {
        'name': '编码转换',
        'icon': 'bi-code-slash',
        'color': '#3498db',
        'description': 'URL、Unicode、进制、大小写等编码转换',
    },
    ToolCategory.TEXT: {
        'name': '文本处理',
        'icon': 'bi-file-text',
        'color': '#2ecc71',
        'description': '文本统计、去重、对比、翻译等',
    },
    ToolCategory.GENERATE: {
        'name': '生成工具',
        'icon': 'bi-magic',
        'color': '#9b59b6',
        'description': 'UUID、密码、二维码、条形码等生成工具',
    },
    ToolCategory.DATA: {
        'name': '数据格式',
        'icon': 'bi-database',
        'color': '#f39c12',
        'description': 'JSON、CSV、HTML、Markdown格式处理',
    },
    ToolCategory.TIME: {
        'name': '时间日期',
        'icon': 'bi-clock',
        'color': '#1abc9c',
        'description': '时间戳转换、时差计算、Cron表达式',
    },
    ToolCategory.IMAGE: {
        'name': '图片工具',
        'icon': 'bi-image',
        'color': '#e91e63',
        'description': '图片压缩、格式转换、Base64、EXIF',
    },
    ToolCategory.NETWORK: {
        'name': '网络工具',
        'icon': 'bi-globe',
        'color': '#00bcd4',
        'description': 'IP查询、端口扫描、HTTP请求等',
    },
    ToolCategory.SECURITY: {
        'name': '安全工具',
        'icon': 'bi-shield-check',
        'color': '#ff5722',
        'description': '密码强度、身份证校验、邮箱验证',
    },
    ToolCategory.CALC: {
        'name': '计算工具',
        'icon': 'bi-calculator',
        'color': '#607d8b',
        'description': 'BMI计算、字节转换、随机数生成',
    },
    ToolCategory.FILE: {
        'name': '文件工具',
        'icon': 'bi-file-earmark',
        'color': '#795548',
        'description': '文件哈希、格式转换',
    },
    ToolCategory.OTHER: {
        'name': '其他工具',
        'icon': 'bi-three-dots',
        'color': '#9e9e9e',
        'description': '其他实用工具',
    },
}

# 分类排序
CATEGORY_ORDER = [
    ToolCategory.ENCRYPT,
    ToolCategory.ENCODE,
    ToolCategory.TEXT,
    ToolCategory.GENERATE,
    ToolCategory.DATA,
    ToolCategory.TIME,
    ToolCategory.IMAGE,
    ToolCategory.NETWORK,
    ToolCategory.SECURITY,
    ToolCategory.CALC,
    ToolCategory.FILE,
    ToolCategory.OTHER,
]
