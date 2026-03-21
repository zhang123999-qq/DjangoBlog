"""
简繁体转换工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import unicodedata


# 简繁体对照表（常用字）
CONVERSION_MAP = {
    # 常用简繁对照
    '电': '電', '网': '網', '号': '號', '万': '萬', '与': '與',
    '义': '義', '为': '為', '乌': '烏', '乐': '樂', '乔': '喬',
    '买': '買', '乱': '亂', '争': '爭', '产': '產', '关': '關',
    '会': '會', '伞': '傘', '备': '備', '车': '車', '马': '馬',
    '东': '東', '丝': '絲', '丢': '丟', '两': '兩', '严': '嚴',
    '丧': '喪', '个': '個', '临': '臨', '丸': '甕', '丹': '冊',
    '主': '主', '乍': '貝', '乏': '負', '乐': '樂', '乒乓': '乒乓球',
    '乔': '喬', '乖': '乘', '乙': '乙', '九': '玖', '乞': '氣',
    '习': '習', '乡': '鄉', '书': '書', '买': '買', '乱': '亂',
}


class ChineseConversionForm(forms.Form):
    """简繁体转换表单"""
    text = forms.CharField(
        label='输入文本',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 6,
            'placeholder': '请输入要转换的文本...'
        }),
        required=True
    )
    conversion_type = forms.ChoiceField(
        label='转换类型',
        choices=[
            ('s2t', '简体 → 繁体'),
            ('t2s', '繁体 → 简体'),
        ],
        initial='s2t',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ChineseConversionTool(BaseTool):
    """简繁体转换工具"""
    name = "简繁体转换"
    slug = "chinese-conversion"
    description = "简体中文与繁体中文相互转换"
    icon = "fa fa-language"
    category = ToolCategory.ENCODE
    form_class = ChineseConversionForm

    # 扩展的简繁对照表
    EXTENDED_MAP_S2T = {
        # 常用词汇
        '软件': '軟體', '硬件': '硬體', '网络': '網路', '电脑': '計算機',
        '手机': '手機', '数据': '資料', '信息': '資訊', '用户': '使用者',
        '管理员': '管理員', '密码': '密碼', '登录': '登錄', '注册': '註冊',
        '设置': '設置', '功能': '功能', '文件': '檔案', '图片': '圖片',
        '视频': '視頻', '音乐': '音樂', '电影': '電影', '游戏': '遊戲',
        '开发': '開發', '代码': '代碼', '程序': '程式', '网站': '網站',
        '服务器': '服務器', '数据库': '數據庫', '系统': '系統', '应用': '應用',
        '学习': '學習', '工作': '工作', '生活': '生活', '时间': '時間',
        '今天': '今天', '明天': '明天', '昨天': '昨天', '现在': '現在',
        '以后': '以后', '之前': '之前', '里面': '裡面', '外面': '外面',
        '什么': '什麼', '怎么': '怎麼', '为什么': '為什麼', '可以': '可以',
        '需要': '需要', '应该': '應該', '可能': '可能', '一定': '一定',
    }

    def s2t(self, text):
        """简体转繁体"""
        result = text
        # 先处理词汇
        for key, value in self.EXTENDED_MAP_S2T.items():
            result = result.replace(key, value)
        # 再处理单字
        for key, value in CONVERSION_MAP.items():
            result = result.replace(key, value)
        return result

    def t2s(self, text):
        """繁体转简体"""
        result = text
        # 反向处理词汇
        for key, value in reversed(list(self.EXTENDED_MAP_S2T.items())):
            result = result.replace(value, key)
        # 反向处理单字
        for key, value in reversed(list(CONVERSION_MAP.items())):
            result = result.replace(value, key)
        return result

    def handle(self, request, form):
        text = form.cleaned_data['text']
        conversion_type = form.cleaned_data['conversion_type']
        
        if conversion_type == 's2t':
            result = self.s2t(text)
            direction = '简体 → 繁体'
        else:
            result = self.t2s(text)
            direction = '繁体 → 简体'
        
        return {
            'original': text,
            'converted': result,
            'direction': direction,
            'original_length': len(text),
            'converted_length': len(result),
        }
