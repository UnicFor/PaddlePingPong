# app_init.py
# 应用工厂函数
# 关键配置：
#   静态文件夹路径：static
#   开发模式启用CORS
#   注册路由蓝图

from flask import Flask
from .config import config_dict
from .extensions import cors, db, executor
from .routes import user_bp, static_bp, auth_bp, frames_bp, video_bp, upload_bp, history_bp, rag_bp


def create_app(config_name='development'):
    # 初始化应用
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # 加载配置
    app.config.from_object(config_dict[config_name])
    executor.init_app(app)

    db.init_app(app)
    from .utils.models import User

    # 配置跨域（仅开发模式）
    cors.init_app(app)
    if config_name == 'development':
        # 使用配置参数方式
        app.config.update({
            'CORS_RESOURCES': {
                r"/api/*": {"origins": "http://localhost:3000"}
            },
            'CORS_SUPPORTS_CREDENTIALS': True
        })

    # 注册蓝图
    # app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(frames_bp, url_prefix='/api')
    app.register_blueprint(video_bp, url_prefix='/api')
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')
    app.register_blueprint(rag_bp, url_prefix='/api')
    app.register_blueprint(static_bp)

    return app