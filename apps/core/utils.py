"""
通用工具函数
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from functools import wraps
import hashlib
from django.utils.text import slugify


def generate_slug(text):
    """生成slug，如果是中文或其他非拉丁字符，使用hash"""
    slug = slugify(text)
    if not slug:
        # 中文或其他非拉丁字符，使用hash
        slug = hashlib.md5(text.encode()).hexdigest()[:8]
    return slug


def toggle_like_view(model_class, like_model_class, related_name='likes', count_field='like_count'):
    """
    通用的点赞/取消点赞视图工厂函数
    
    Args:
        model_class: 被点赞的模型类
        like_model_class: 点赞记录模型类
        related_name: 点赞关系的字段名
        count_field: 点赞计数的字段名
    
    Returns:
        function: 视图函数
    """
    @login_required
    def view(request, obj_id):
        # 获取对象
        obj = model_class.objects.filter(pk=obj_id).first()
        if not obj:
            return JsonResponse({
                'success': False,
                'message': '对象不存在'
            })
        
        # 检查审核状态
        if hasattr(obj, 'review_status') and obj.review_status != 'approved':
            return JsonResponse({
                'success': False,
                'message': '只能对已审核通过的内容点赞'
            })
        
        # 获取或创建点赞记录
        like, created = like_model_class.objects.get_or_create(
            user=request.user,
            **{related_name.replace('likes', 'comment') if 'comment' in related_name else related_name.rstrip('s'): obj}
        )
        
        if not created:
            # 已经点赞，取消点赞
            like.delete()
            liked = False
        else:
            # 新点赞
            liked = True
        
        # 更新点赞数
        if hasattr(obj, count_field):
            likes_manager = getattr(obj, related_name)
            setattr(obj, count_field, likes_manager.count())
            obj.save(update_fields=[count_field])
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'like_count': getattr(obj, count_field, 0),
            'message': '操作成功'
        })
    
    return view


def require_ajax(view_func):
    """要求AJAX请求的装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '无效请求'}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper
