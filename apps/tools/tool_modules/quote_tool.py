"""
名言警句工具
"""
from django import forms
from apps.tools.base_tool import BaseTool
import random


class QuoteForm(forms.Form):
    """名言警句表单"""
    category = forms.ChoiceField(
        label='选择类别',
        choices=[
            ('all', '全部'),
            ('motivation', '励志'),
            ('wisdom', '智慧'),
            ('life', '人生'),
            ('study', '学习'),
            ('success', '成功'),
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    count = forms.IntegerField(
        label='生成数量',
        min_value=1,
        max_value=10,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'}))


class QuoteTool(BaseTool):
    """名言警句工具"""
    name = "名言警句"
    slug = "famous-quote"
    description = "随机生成经典名言警句"
    icon = "fa fa-quote-left"
    form_class = QuoteForm

    QUOTES = [
        {'text': '天行健，君子以自强不息', 'author': '周易', 'category': 'wisdom'},
        {'text': '千里之行，始于足下', 'author': '老子', 'category': 'wisdom'},
        {'text': '学而不思则罔，思而不学则殆', 'author': '孔子', 'category': 'study'},
        {'text': '知之者不如好之者，好之者不如乐之者', 'author': '孔子', 'category': 'study'},
        {'text': '天才是1%的灵感加99%的汗水', 'author': '爱迪生', 'category': 'motivation'},
        {'text': '失败是成功之母', 'author': '谚语', 'category': 'success'},
        {'text': '世上无难事，只要肯攀登', 'author': '毛泽东', 'category': 'motivation'},
        {'text': '人生如逆旅，我亦是行人', 'author': '苏轼', 'category': 'life'},
        {'text': '不以物喜，不以己悲', 'author': '范仲淹', 'category': 'life'},
        {'text': '先天下之忧而忧，后天下之乐而乐', 'author': '范仲淹', 'category': 'wisdom'},
        {'text': '路漫漫其修远兮，吾将上下而求索', 'author': '屈原', 'category': 'motivation'},
        {'text': '书山有路勤为径，学海无涯苦作舟', 'author': '韩愈', 'category': 'study'},
        {'text': '锲而不舍，金石可镂', 'author': '荀子', 'category': 'motivation'},
        {'text': '生于忧患，死于安乐', 'author': '孟子', 'category': 'wisdom'},
        {'text': '只要功夫深，铁杵磨成针', 'author': '谚语', 'category': 'motivation'},
    ]

    def handle(self, request, form):
        category = form.cleaned_data['category']
        count = form.cleaned_data['count']
        
        # 根据类别筛选
        if category == 'all':
            quotes = self.QUOTES
        else:
            quotes = [q for q in self.QUOTES if q['category'] == category]
        
        # 随机选择
        selected = random.sample(quotes, min(count, len(quotes)))
        
        return {
            'quotes': selected,
            'count': len(selected),
        }
