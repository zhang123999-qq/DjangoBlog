"""
哈希文件校验工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import hashlib


class FileHashForm(forms.Form):
    """哈希文件校验表单"""
    file = forms.FileField(
        label='上传文件',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    algorithm = forms.ChoiceField(
        label='哈希算法',
        choices=[
            ('md5', 'MD5'),
            ('sha1', 'SHA1'),
            ('sha256', 'SHA256'),
        ],
        initial='md5',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class FileHashTool(BaseTool):
    """哈希文件校验工具"""
    name = "文件哈希校验"
    slug = "file-hash"
    description = "计算上传文件的MD5/SHA1/SHA256哈希值"
    icon = "fa fa-file-check"
    category = ToolCategory.FILE
    form_class = FileHashForm

    def handle(self, request, form):
        uploaded_file = form.cleaned_data['file']
        algorithm = form.cleaned_data['algorithm']
        
        try:
            # 选择哈希算法
            if algorithm == 'md5':
                hash_obj = hashlib.md5()
            elif algorithm == 'sha1':
                hash_obj = hashlib.sha1()
            elif algorithm == 'sha256':
                hash_obj = hashlib.sha256()
            else:
                return {'error': '不支持的哈希算法'}
            
            # 分块读取文件并更新哈希
            for chunk in uploaded_file.chunks():
                hash_obj.update(chunk)
            
            # 获取哈希值
            hash_value = hash_obj.hexdigest()
            
            return {
                'filename': uploaded_file.name,
                'algorithm': algorithm.upper(),
                'hash_value': hash_value
            }
        except Exception as e:
            return {'error': str(e)}
