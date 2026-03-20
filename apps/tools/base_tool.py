class BaseTool:
    """工具基类"""
    name = "工具"
    slug = "tool"
    description = "工具描述"
    icon = "tools"
    template_name = "tools/tool_detail_tech.html"
    form_class = None

    def get_form(self, data=None, files=None):
        """获取表单实例"""
        if self.form_class:
            return self.form_class(data, files)
        return None

    def get_context(self, request, form=None, result=None):
        """获取上下文数据"""
        return {
            'tool': self,
            'form': form,
            'result': result,
        }

    def handle(self, request, form):
        """处理工具逻辑，返回结果"""
        raise NotImplementedError("子类必须实现 handle 方法")
