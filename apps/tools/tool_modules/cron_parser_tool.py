"""
Cron表达式解析工具
"""
from django import forms
from apps.tools.base_tool import BaseTool


class CronParserForm(forms.Form):
    """Cron表达式解析表单"""
    cron_expression = forms.CharField(
        label='Cron表达式',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0 9 * * 1'}),
        required=True
    )


class CronParserTool(BaseTool):
    """Cron表达式解析工具"""
    name = "Cron表达式解析"
    slug = "cron-parser"
    description = "解析Cron表达式，显示下次执行时间或人类可读描述"
    icon = "fa fa-clock"
    form_class = CronParserForm

    def handle(self, request, form):
        cron_expression = form.cleaned_data['cron_expression']
        
        try:
            from croniter import croniter
            import datetime
        except ImportError:
            return {'error': '请安装 croniter: pip install croniter'}
        
        try:
            # 解析Cron表达式
            now = datetime.datetime.now()
            cron = croniter(cron_expression, now)
            
            # 获取未来5次执行时间
            next_executions = []
            for i in range(5):
                next_time = cron.get_next(datetime.datetime)
                next_executions.append(next_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            # 生成人类可读描述
            parts = cron_expression.split()
            if len(parts) != 5:
                return {'error': 'Cron表达式格式错误，应为5个字段'}
            
            minute, hour, day, month, weekday = parts
            
            # 解析分钟
            if minute == '0':
                minute_desc = '整点'
            elif minute == '*':
                minute_desc = '每分钟'
            else:
                minute_desc = f'{minute}分'
            
            # 解析小时
            if hour == '*':
                hour_desc = '每小时'
            else:
                hour_desc = f'{hour}时'
            
            # 解析日期
            if day == '*':
                day_desc = '每天'
            else:
                day_desc = f'{day}日'
            
            # 解析月份
            if month == '*':
                month_desc = '每月'
            else:
                month_desc = f'{month}月'
            
            # 解析星期
            weekday_map = {
                '0': '周日', '1': '周一', '2': '周二', '3': '周三',
                '4': '周四', '5': '周五', '6': '周六', '*': '每天'
            }
            weekday_desc = weekday_map.get(weekday, weekday)
            
            human_readable = f'{month_desc}{day_desc}{weekday_desc} {hour_desc}{minute_desc}'
            
            return {
                'cron_expression': cron_expression,
                'human_readable': human_readable,
                'next_executions': next_executions
            }
        except Exception as e:
            return {'error': str(e)}
