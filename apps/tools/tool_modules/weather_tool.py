"""
天气查询工具（支持多个 API 源作为 fallback）
"""

from ..categories import ToolCategory
from django import forms
from django.conf import settings
from apps.tools.base_tool import BaseTool
import requests


class WeatherForm(forms.Form):
    """天气查询表单"""

    city = forms.CharField(
        label="城市名称",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "输入城市名称，如：北京"}),
        required=True,
    )
    unit = forms.ChoiceField(
        label="温度单位",
        choices=[
            ("celsius", "摄氏度 (°C)"),
            ("fahrenheit", "华氏度 (°F)"),
        ],
        initial="celsius",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class WeatherTool(BaseTool):
    """天气查询工具（多源 fallback）"""

    name = "天气查询"
    slug = "weather"
    description = "查询指定城市的天气信息（多数据源，一个失败自动切换）"
    icon = "fa fa-cloud"
    category = ToolCategory.NETWORK
    form_class = WeatherForm

    def handle(self, request, form):
        city = form.cleaned_data["city"]
        unit = form.cleaned_data["unit"]

        # 从 .env 读取 API Key，如果未配置则回退到公共 API
        api_key = getattr(settings, "OPENWEATHER_API_KEY", None)

        # 来源 1: OpenWeatherMap（需要 API Key，数据最全）
        if api_key and api_key != "YOUR_API_KEY":
            result = self._query_openweather(city, unit, api_key)
            if result and "error" not in result:
                result["source"] = "OpenWeatherMap"
                return result

        # 来源 2: wttr.in（免费无需 API Key）
        result = self._query_wttr(city, unit)
        if result and "error" not in result:
            result["source"] = "wttr.in"
            return result

        # 全部失败
        return {
            "error": "天气查询服务暂时不可用，请稍后重试。",
            "city": city,
        }

    def _query_openweather(self, city, unit, api_key):
        """OpenWeatherMap API 查询"""
        try:
            base_url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": api_key,
                "lang": "zh_cn",
                "units": "metric" if unit == "celsius" else "imperial",
            }
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()

            if response.status_code == 200:
                return {
                    "city": data.get("name"),
                    "country": data.get("sys", {}).get("country"),
                    "temperature": data.get("main", {}).get("temp"),
                    "feels_like": data.get("main", {}).get("feels_like"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "weather": data.get("weather", [{}])[0].get("description"),
                    "icon": data.get("weather", [{}])[0].get("icon"),
                    "wind_speed": data.get("wind", {}).get("speed"),
                    "unit": "°C" if unit == "celsius" else "°F",
                }
        except Exception:
            pass
        return None

    def _query_wttr(self, city, unit):
        """wttr.in 免费天气 API（无需 Key）"""
        try:
            # wttr.in 支持中文返回
            fmt = "%C,%t,%h,%w,%p"
            url = f"https://wttr.in/{city}?format={fmt}&lang=zh-cn"
            response = requests.get(url, headers={"User-Agent": "DjangoBlog"}, timeout=10)

            if response.status_code == 200:
                text = response.text.strip()
                parts = text.split(",")
                if len(parts) >= 5:
                    return {
                        "city": city,
                        "weather": parts[0].strip(),
                        "temperature": parts[1].strip(),
                        "humidity": parts[2].strip(),
                        "wind_speed": parts[3].strip(),
                        "precipitation": parts[4].strip(),
                        "unit": "°C" if unit == "celsius" else "°F",
                    }
        except Exception:
            pass
        return None
