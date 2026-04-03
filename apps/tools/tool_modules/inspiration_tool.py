"""
灵感文库：古诗词 + 名言警句
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import random


class InspirationForm(forms.Form):
    """灵感文库表单"""
    content_type = forms.ChoiceField(
        label='内容类型',
        choices=[
            ('poem', '古诗词'),
            ('quote', '名言警句'),
            ('both', '古诗词 + 名言'),
        ],
        initial='poem',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category = forms.ChoiceField(
        label='筛选类别',
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
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class InspirationTool(BaseTool):
    """灵感文库工具（古诗词 + 名言警句）"""
    name = "灵感文库"
    slug = "inspiration"
    description = "随机生成经典古诗词和名言警句，获取写作灵感与人生智慧"
    icon = "fa fa-book-open"
    category = ToolCategory.TEXT
    form_class = InspirationForm

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
        {'title': '枫桥夜泊', 'author': '张继', 'content': '月落乌啼霜满天，江枫渔火对愁眠。\n姑苏城外寒山寺，夜半钟声到客船。', 'dynasty': '唐'},
        {'title': '早发白帝城', 'author': '李白', 'content': '朝辞白帝彩云间，千里江陵一日还。\n两岸猿声啼不住，轻舟已过万重山。', 'dynasty': '唐'},
        {'title': '望庐山瀑布', 'author': '李白', 'content': '日照香炉生紫烟，遥看瀑布挂前川。\n飞流直下三千尺，疑是银河落九天。', 'dynasty': '唐'},
        {'title': '黄鹤楼送孟浩然之广陵', 'author': '李白', 'content': '故人西辞黄鹤楼，烟花三月下扬州。\n孤帆远影碧空尽，唯见长江天际流。', 'dynasty': '唐'},
        {'title': '水调歌头', 'author': '苏轼', 'content': '明月几时有？把酒问青天。\n不知天上宫阙，今夕是何年。\n我欲乘风归去，又恐琼楼玉宇，高处不胜寒。', 'dynasty': '宋'},
        {'title': '念奴娇·赤壁怀古', 'author': '苏轼', 'content': '大江东去，浪淘尽，千古风流人物。\n故垒西边，人道是，三国周郎赤壁。\n乱石穿空，惊涛拍岸，卷起千堆雪。', 'dynasty': '宋'},
        {'title': '声声慢', 'author': '李清照', 'content': '寻寻觅觅，冷冷清清，凄凄惨惨戚戚。\n乍暖还寒时候，最难将息。\n三杯两盏淡酒，怎敌他、晚来风急。', 'dynasty': '宋'},
        {'title': '虞美人', 'author': '李煜', 'content': '春花秋月何时了？往事知多少。\n小楼昨夜又东风，故国不堪回首月明中。\n问君能有几多愁？恰似一江春水向东流。', 'dynasty': '宋'},
    ]

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
        {'text': '三人行，必有我师焉', 'author': '孔子', 'category': 'study'},
        {'text': '海纳百川，有容乃大', 'author': '林则徐', 'category': 'wisdom'},
        {'text': '知人者智，自知者明', 'author': '老子', 'category': 'wisdom'},
        {'text': '不积跬步，无以至千里', 'author': '荀子', 'category': 'motivation'},
        {'text': '老骥伏枥，志在千里', 'author': '曹操', 'category': 'motivation'},
    ]

    def handle(self, request, form):
        content_type = form.cleaned_data['content_type']
        category = form.cleaned_data['category']
        count = form.cleaned_data['count']

        result = {
            'poems': [],
            'quotes': [],
        }

        if content_type in ('poem', 'both'):
            result['poems'] = self._get_poems(category, count)

        if content_type in ('quote', 'both'):
            result['quotes'] = self._get_quotes(category, count) if content_type == 'quote' else self._get_quotes('all', count)

        return result

    def _get_poems(self, category, count):
        """获取古诗词（去重后随机选取）"""
        # 用 title + author 去重
        seen = set()
        unique_poems = []
        for p in self.POEMS:
            key = f"{p['title']}|{p['author']}"
            if key not in seen:
                seen.add(key)
                unique_poems.append(p)

        return random.sample(unique_poems, min(count, len(unique_poems)))

    def _get_quotes(self, category, count):
        """获取名言警句"""
        if category == 'all':
            quotes = self.QUOTES
        else:
            quotes = [q for q in self.QUOTES if q['category'] == category]

        return random.sample(quotes, min(count, len(quotes)))
