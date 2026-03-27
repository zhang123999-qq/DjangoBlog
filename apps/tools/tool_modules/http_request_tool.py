"""
HTTP请求模拟器工具 - 优化版
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import json


class HTTPRequestForm(forms.Form):
    """HTTP请求模拟器表单"""
    url = forms.CharField(
        label='URL',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://api.example.com/endpoint'
        }),
        required=True,
        help_text='输入完整的URL地址'
    )
    method = forms.ChoiceField(
        label='请求方法',
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('DELETE', 'DELETE'),
            ('PATCH', 'PATCH'),
            ('HEAD', 'HEAD'),
            ('OPTIONS', 'OPTIONS'),
        ],
        initial='GET',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    headers = forms.CharField(
        label='请求头（JSON格式）',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': '{"Content-Type": "application/json", "Authorization": "Bearer token"}'
        }),
        required=False,
        help_text='可选的请求头，JSON格式'
    )
    data = forms.CharField(
        label='请求体（POST/PUT/PATCH）',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'class': 'form-control',
            'placeholder': '{"key": "value"}'
        }),
        required=False,
        help_text='请求体内容，JSON或表单格式'
    )
    content_type = forms.ChoiceField(
        label='Content-Type',
        choices=[
            ('application/json', 'JSON'),
            ('application/x-www-form-urlencoded', '表单'),
            ('text/plain', '纯文本'),
            ('multipart/form-data', 'multipart'),
        ],
        initial='application/json',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    timeout = forms.IntegerField(
        label='超时时间（秒）',
        min_value=1,
        max_value=60,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    follow_redirects = forms.BooleanField(
        label='跟随重定向',
        initial=True,
        required=False,
        help_text='是否自动跟随301/302重定向'
    )


class HTTPRequestTool(BaseTool):
    """HTTP请求模拟器工具"""
    name = "HTTP请求模拟器"
    slug = "http-request"
    description = "发送HTTP/HTTPS请求，支持多种方法、自定义头部和请求体"
    icon = "fa fa-paper-plane"
    category = ToolCategory.NETWORK
    form_class = HTTPRequestForm

    def handle(self, request, form):
        url = form.cleaned_data['url']
        method = form.cleaned_data['method']
        headers = form.cleaned_data['headers']
        data = form.cleaned_data['data']
        content_type = form.cleaned_data['content_type']
        timeout = form.cleaned_data['timeout']
        follow_redirects = form.cleaned_data['follow_redirects']

        try:
            import requests
        except ImportError:
            return {'error': '请安装 requests: pip install requests'}

        try:
            # 解析请求头
            headers_dict = {}
            if headers:
                try:
                    headers_dict = json.loads(headers)
                except json.JSONDecodeError as e:
                    return {'error': f'请求头JSON解析错误: {str(e)}'}

            # 添加Content-Type
            if method in ['POST', 'PUT', 'PATCH'] and data:
                headers_dict['Content-Type'] = content_type

            # 发送请求
            session = requests.Session()

            if method == 'GET':
                response = session.get(
                    url,
                    headers=headers_dict,
                    timeout=timeout,
                    allow_redirects=follow_redirects
                )
            elif method == 'POST':
                if content_type == 'application/json' and data:
                    try:
                        data = json.loads(data)
                    except Exception:
                        pass
                response = session.post(
                    url,
                    data=data,
                    headers=headers_dict,
                    timeout=timeout,
                    allow_redirects=follow_redirects
                )
            elif method == 'PUT':
                if content_type == 'application/json' and data:
                    try:
                        data = json.loads(data)
                    except Exception:
                        pass
                response = session.put(
                    url,
                    data=data,
                    headers=headers_dict,
                    timeout=timeout,
                    allow_redirects=follow_redirects
                )
            elif method == 'DELETE':
                response = session.delete(
                    url,
                    headers=headers_dict,
                    timeout=timeout,
                    allow_redirects=follow_redirects
                )
            elif method == 'PATCH':
                if content_type == 'application/json' and data:
                    try:
                        data = json.loads(data)
                    except Exception:
                        pass
                response = session.patch(
                    url,
                    data=data,
                    headers=headers_dict,
                    timeout=timeout,
                    allow_redirects=follow_redirects
                )
            elif method == 'HEAD':
                response = session.head(
                    url,
                    headers=headers_dict,
                    timeout=timeout,
                    allow_redirects=follow_redirects
                )
            elif method == 'OPTIONS':
                response = session.options(
                    url,
                    headers=headers_dict,
                    timeout=timeout,
                    allow_redirects=follow_redirects
                )

            # 解析响应
            result = {
                'url': response.url,
                'method': method,
                'status_code': response.status_code,
                'status_text': response.reason,
                'headers': dict(response.headers),
            }

            # 响应时间
            result['response_time'] = f"{response.elapsed.total_seconds() * 1000:.2f}ms"

            # 响应内容
            if method != 'HEAD':
                try:
                    # 尝试解析为JSON
                    result['content'] = response.json()
                    result['content_type'] = 'json'
                except Exception:
                    # 返回文本
                    result['content'] = response.text[:5000] if len(response.text) > 5000 else response.text
                    result['content_type'] = 'text'

                # 内容编码
                result['encoding'] = response.encoding

            # Cookies
            if response.cookies:
                result['cookies'] = dict(response.cookies)

            return result

        except requests.Timeout:
            return {'error': '请求超时'}
        except requests.ConnectionError as e:
            return {'error': f'连接错误: {str(e)}'}
        except requests.RequestException as e:
            return {'error': f'请求错误: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'error': f'请求体JSON解析错误: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}
