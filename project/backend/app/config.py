# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    STATIC_FOLDER = str(BASE_DIR / 'app/static')

    FRAME_FOLDER = str(BASE_DIR / 'app/data/frame')  # 测试帧路径
    UPLOAD_FOLDER = os.path.abspath('./data/video')  # 测试视频路径
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB限制

    STATIC_URL_PATH = ''

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    CORS_ORIGINS = ['http://localhost:3000']
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_EXPOSE_HEADERS = ['Content-Disposition']

class ProductionConfig(BaseConfig):
    DEBUG = False

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}