
import os
import sys

# Add the project to Python path
sys.path.insert(0, '/mnt/f/DjangoBlog')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoBlog.settings')

print("=== 测试导入 ===")
try:
    import django
    print(f"✅ Django version: {django.VERSION}")
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup error: {e}")
    import traceback
    traceback.print_exc()

try:
    from apps.blog.models import Comment, CommentLike
    print("✅ Comment and CommentLike models imported")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

try:
    from apps.blog.forms import CommentForm
    print("✅ CommentForm imported")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")
