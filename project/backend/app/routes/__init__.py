# router_init.py
# 作用:导出API和静态文件路由蓝图
# 说明:作为路由模块的入口文件,集中管理所有路由蓝图

from .static import static_bp
from .auth import auth_bp
from .user import user_bp
from .upload import upload_bp
from .history import history_bp
from .video import video_bp
from .frames import frames_bp
from .rag import rag_bp

__all__ = ['static_bp',
           'auth_bp',
           'user_bp',
           'upload_bp',
           'history_bp',
           'frames_bp',
           'video_bp',
           'rag_bp'
           ]