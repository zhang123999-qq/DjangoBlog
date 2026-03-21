"""
古诗生成器
"""
from ..categories import ToolCategory
from django import forms
from django.http import HttpResponse
from apps.tools.base_tool import BaseTool
import random


class PoemForm(forms.Form):
    """古诗生成器表单"""
    category = forms.ChoiceField(
        label='选择类别',
        choices=[
            ('all', '全部'),
            ('tang', '唐诗'),
            ('song', '宋词'),
            ('five', '五言绝句'),
            ('seven', '七言绝句'),
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    count = forms.IntegerField(
        label='生成数量',
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}))


class PoemGeneratorTool(BaseTool):
    """古诗生成器工具"""
    name = "古诗生成"
    slug = "poem-generator"
    description = "随机生成经典古诗词"
    icon = "fa fa-scroll"
    form_class = PoemForm

    POEMS = [
        {'title': '静夜思', 'author': '李白', 'content': '床前明月光，疑是地上霜。\n举头望明月，低头思故乡。', 'dynasty': '唐'},
        {'title': '春晓', 'author': '孟浩然', 'content': '春眠不觉晓，处处闻啼鸟。\n夜来风雨声，花落知多少。', 'dynasty': '唐'},
        {'title': '登鹳雀楼', 'author': '王之涣', 'content': '白日依山尽，黄河入海流。\n欲穷千里目，更上一层楼。', 'dynasty': '唐'},
        {'title': '相思', 'author': '王维', 'content': '红豆生南国，春来发几枝。\n愿君多采撷，此物最相思。', 'dynasty': '唐'},
        {'title': '鹿柴', 'author': '王维', 'content': '空山不见人，但闻人语响。\n返景入深林，复照青苔上。', 'dynasty': '唐'},
        {'title': '江雪', 'author': '柳宗元', 'content': '千山鸟飞绝，万径人踪灭。\n孤舟蓑笠翁，独钓寒江雪。', 'dynasty': '唐'},
        {'title': '悯农', 'author': '李绅', 'content': '锄禾日当午，汗滴禾下土。\n谁知盘中餐，粒粒皆辛苦。', 'dynasty': '唐'},
        {'title': '游子吟', 'author': '孟郊', 'content': '慈母手中线，游子身上衣。\n临行密密缝，意恐迟迟归。', 'dynasty': '唐'},
        {'title': '绝句', 'author': '杜甫', 'content': '两个黄鹂鸣翠柳，一行白鹭上青天。\n窗含西岭千秋雪，门泊东吴万里船。', 'dynasty': '唐'},
        {'title': '清明', 'author': '杜牧', 'content': '清明时节雨纷纷，路上行人欲断魂。\n借问酒家何处有，牧童遥指杏花村。', 'dynasty': '唐'},
        {'title': '咏鹅', 'author': '骆宾王', 'content': '鹅鹅鹅，曲项向天歌。\n白毛浮绿水，红掌拨清波。', 'dynasty': '唐'},
        {'title': '赋得古原草送别', 'author': '白居易', 'content': '离离原上草，一岁一枯荣。\n野火烧不尽，春风吹又生。', 'dynasty': '唐'},
        {'title': '静夜思', 'author': '李白', 'content': '床前明月光，疑是地上霜。\n举头望明月，低头思故乡。', 'dynasty': '唐'},
        {'title': '枫桥夜泊', 'author': '张继', 'content': '月落乌啼霜满天，江枫渔火对愁眠。\n姑苏城外寒山寺，夜半钟声到客船。', 'dynasty': '唐'},
        {'title': '早发白帝城', 'author': '李白', 'content': '朝辞白帝彩云间，千里江陵一日还。\n两岸猿声啼不住，轻舟已过万重山。', 'dynasty': '唐'},
    ]

    def handle(self, request, form):
        category = form.cleaned_data['category']
        count = form.cleaned_data['count']
        
        # 根据类别筛选
        if category == 'all':
            poems = self.POEMS
        else:
            poems = self.POEMS  # 简化处理，全部返回
        
        # 随机选择
        selected = random.sample(poems, min(count, len(poems)))
        
        return {
            'poems': selected,
            'count': len(selected),
        }
