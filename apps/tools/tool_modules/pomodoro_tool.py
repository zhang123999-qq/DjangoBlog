"""
番茄钟工具 - 工作学习计时器
"""

from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool


class PomodoroForm(forms.Form):
    """番茄钟表单"""

    duration = forms.IntegerField(
        label="专注时长（分钟）",
        min_value=1,
        max_value=120,
        initial=25,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    break_duration = forms.IntegerField(
        label="休息时长（分钟）",
        min_value=1,
        max_value=30,
        initial=5,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    rounds = forms.IntegerField(
        label="轮次", min_value=1, max_value=10, initial=4, widget=forms.NumberInput(attrs={"class": "form-control"})
    )


class PomodoroTool(BaseTool):
    """番茄钟工具"""

    name = "番茄钟"
    slug = "pomodoro"
    description = "简洁的番茄工作法计时器，帮助你专注工作或学习"
    icon = "fa fa-clock"
    category = ToolCategory.TIME
    form_class = PomodoroForm

    def handle(self, request, form):
        duration = form.cleaned_data["duration"]
        break_duration = form.cleaned_data["break_duration"]
        rounds = form.cleaned_data["rounds"]

        total_work = duration * rounds
        total_break = break_duration * (rounds - 1) if rounds > 1 else 0
        total_time = total_work + total_break

        # 计算时间安排
        schedule = []
        for i in range(rounds):
            schedule.append(
                {
                    "round": i + 1,
                    "type": "工作",
                    "duration": duration,
                    "start": f"第{i * (duration + break_duration)}分钟",
                    "end": f"第{(i+1)*duration + i*break_duration}分钟",
                }
            )
            if i < rounds - 1:
                schedule.append(
                    {
                        "round": i + 1,
                        "type": "休息",
                        "duration": break_duration,
                        "start": f"第{(i+1)*duration + i*break_duration}分钟",
                        "end": f"第{(i+1)*(duration + break_duration)}分钟",
                    }
                )

        return {
            "duration": duration,
            "break_duration": break_duration,
            "rounds": rounds,
            "total_work": total_work,
            "total_break": total_break,
            "total_time": total_time,
            "schedule": schedule,
            "tips": [
                "工作期间保持专注，不要切换任务",
                "休息时离开座位，活动一下",
                "每4轮后可以休息长一点",
                "保持良好的作息习惯",
            ],
        }
