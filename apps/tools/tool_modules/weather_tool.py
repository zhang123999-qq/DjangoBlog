"""
天气查询工具
"""
from django import forms
from apps.tools.base_tool import BaseTool
import requests


class WeatherForm(forms.Form):
    """天气查询表单"""
    city = forms.CharField(
        label='城市名称',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入城市名称，如：北京'}),
        required=True
    )
    unit = forms.ChoiceField(
        label='温度单位',
        choices=[
            ('celsius', '摄氏度 (°C)'),
            ('fahrenheit', '华氏度 (°F)'),
        ],
        initial='celsius',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class WeatherTool(BaseTool):
    """天气查询工具"""
    name = "天气查询"
    slug = "weather"
    description = "查询指定城市的天气信息"
    icon = "fa fa-cloud"
    form_class = WeatherForm

    def handle(self, request, form):
        city = form.cleaned_data['city']
        unit = form.cleaned_data['unit']
        
        try:
            # 使用OpenWeatherMap API查询天气
            # 注意：这里使用了一个示例API密钥，实际使用时需要替换为真实的API密钥
            api_key = "YOUR_API_KEY"
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": api_key,
                "lang": "zh_cn",
                "units": "metric" if unit == "celsius" else "imperial"
            }
            
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                weather_data = {
                    "city": data.get("name"),
                    "country": data.get("sys", {}).get("country"),
                    "temperature": data.get("main", {}).get("temp"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "weather": data.get("weather", [{}])[0].get("description"),
                    "wind_speed": data.get("wind", {}).get("speed"),
                    "unit": unit
                }
                return weather_data
            else:
                return {"error": f"查询失败: {data.get('message', '未知错误')}"}
        except Exception as e:
            return {"error": f"查询失败: {str(e)}"}
