"""
文件格式转换工具
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import os
import tempfile


class FileConverterForm(forms.Form):
    """文件格式转换表单"""
    file = forms.FileField(
        label='上传文件',
        widget=forms.FileInput(attrs={'class': 'form-control-file'}),
        required=True
    )
    output_format = forms.ChoiceField(
        label='输出格式',
        choices=[
            ('pdf', 'PDF'),
            ('docx', 'Word文档'),
            ('txt', '文本文件'),
            ('jpg', 'JPG图片'),
            ('png', 'PNG图片'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class FileConverterTool(BaseTool):
    """文件格式转换工具"""
    name = "文件格式转换"
    slug = "file-converter"
    description = "将不同格式的文件转换为其他格式"
    icon = "fa fa-file-convert"
    category = ToolCategory.FILE
    form_class = FileConverterForm

    def handle(self, request, form):
        uploaded_file = form.cleaned_data['file']
        output_format = form.cleaned_data['output_format']

        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name

            # 模拟文件转换（实际实现需要根据不同格式使用相应的库）
            # 这里只是一个示例，实际实现需要根据具体格式使用相应的库
            output_file_path = f"{temp_file_path}.{output_format}"

            # 简单复制文件作为示例
            with open(temp_file_path, 'rb') as f_in, open(output_file_path, 'wb') as f_out:
                f_out.write(f_in.read())

            # 清理临时文件
            os.unlink(temp_file_path)

            # 注意：实际实现中，这里应该返回转换后的文件供用户下载
            # 这里只是返回一个成功消息
            return {
                "original_file": uploaded_file.name,
                "output_format": output_format,
                "message": f"文件 {uploaded_file.name} 已成功转换为 {output_format} 格式"
            }
        except Exception as e:
            return {"error": f"转换失败: {str(e)}"}
