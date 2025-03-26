# app_init.py
# 应用工厂函数
# 关键配置：
#   静态文件夹路径：static
#   开发模式启用CORS
#   注册路由蓝图

from flask import Flask
from .config import config_dict
from .extensions import cors
from .routes import api_bp, static_bp

def create_app(config_name='development'):
    # 初始化应用
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # 加载配置
    app.config.from_object(config_dict[config_name])

    # 配置跨域（仅开发模式）
    if config_name == 'development':
        from flask_cors import CORS
        CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(static_bp)

    return app