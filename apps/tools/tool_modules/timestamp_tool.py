"""
时间戳转换工具
"""
import time
from datetime import datetime
from django import forms
from apps.tools.base_tool import BaseTool


class TimestampForm(forms.Form):
    """时间戳表单"""
    mode = forms.ChoiceField(
        label='转换方式',
        choices=[
            ('timestamp', '日期时间 → 时间戳'),
            ('datetime', '时间戳 → 日期时间'),
            ('now', '获取当前时间戳'),
        ],
        initial='now',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'timestamp-mode'})
    )
    input_value = forms.CharField(
        label='输入值',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '留空则使用当前时间'})
    )


class TimestampTool(BaseTool):
    """时间戳转换工具"""
    name = "时间戳转换"
    slug = "timestamp"
    description = "时间戳与日期时间互转"
    icon = "fa fa-clock"
    form_class = TimestampForm

    def handle(self, request, form):
        mode = form.cleaned_data['mode']
        input_value = form.cleaned_data.get('input_value', '')
        
        try:
            if mode == 'now':
                now = datetime.now()
                return {
                    'mode': mode,
                    'timestamp': int(now.timestamp()),
                    'timestamp_ms': int(now.timestamp() * 1000),
                    'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'iso': now.isoformat(),
                }
            elif mode == 'timestamp':
                # 日期时间转时间戳
                if not input_value:
                    dt = datetime.now()
                else:
                    # 尝试多种格式
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d',
                        '%Y/%m/%d %H:%M:%S',
                        '%Y/%m/%d',
                    ]
                    dt = None
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(input_value, fmt)
                            break
                        except:
                            continue
                    
                    if not dt:
                        return {'error': '日期格式不正确，支持: YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD'}
                
                return {
                    'mode': mode,
                    'input': input_value or '当前时间',
                    'timestamp': int(dt.timestamp()),
                    'timestamp_ms': int(dt.timestamp() * 1000),
                }
            else:
                # 时间戳转日期时间
                ts = int(input_value) if input_value else int(time.time())
                
                # 毫秒时间戳处理
                if ts > 10000000000:
                    ts = ts / 1000
                
                dt = datetime.fromtimestamp(ts)
                
                return {
                    'mode': mode,
                    'input': input_value,
                    'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M:%S'),
                    'iso': dt.isoformat(),
                }
        except Exception as e:
            return {'error': str(e)}
