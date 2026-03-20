"""
时间差计算器
"""
from django import forms
from apps.tools.base_tool import BaseTool
from datetime import datetime


class TimeDiffForm(forms.Form):
    """时间差计算表单"""
    start_date = forms.DateTimeField(
        label='开始时间',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        required=True
    )
    end_date = forms.DateTimeField(
        label='结束时间',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        required=True
    )


class TimeDiffTool(BaseTool):
    """时间差计算工具"""
    name = "时间差计算"
    slug = "time-diff"
    description = "计算两个日期时间之间的时间差"
    icon = "fa fa-calendar-alt"
    form_class = TimeDiffForm

    def handle(self, request, form):
        start = form.cleaned_data['start_date']
        end = form.cleaned_data['end_date']
        
        # 计算差值
        diff = end - start
        
        total_seconds = int(diff.total_seconds())
        
        # 分解
        days = diff.days
        hours = total_seconds % 86400 // 3600
        minutes = total_seconds % 3600 // 60
        seconds = total_seconds % 60
        
        # 周数
        weeks = days // 7
        remaining_days = days % 7
        
        # 月数（估算）
        months = days // 30
        remaining_days_month = days % 30
        
        # 年数（估算）
        years = days // 365
        remaining_days_year = days % 365
        
        return {
            'start': start.strftime('%Y-%m-%d %H:%M:%S'),
            'end': end.strftime('%Y-%m-%d %H:%M:%S'),
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'total_seconds': total_seconds,
            'weeks': weeks,
            'remaining_days': remaining_days,
            'months': months,
            'remaining_days_month': remaining_days_month,
            'years': years,
            'remaining_days_year': remaining_days_year,
            'formatted': f"{days}天 {hours}小时 {minutes}分钟" if days > 0 else f"{hours}小时 {minutes}分钟 {seconds}秒",
        }
