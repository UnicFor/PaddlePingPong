# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:20221625@localhost/fwwb?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STATIC_FOLDER = str(BASE_DIR / 'app/static')

    UTILS_FOLDER = str(BASE_DIR / 'app/utils/video')

    FRAMES_FOLDER = str(BASE_DIR / 'app/utils/frames')  # 处理帧路径
    PROCESSED_FOLDER = str(BASE_DIR / 'app/utils/video/output')  # 处理视频路径
    POSE_FOLDER = str(BASE_DIR / 'app/utils/video/output_pose')  # 骨骼路径
    UPLOAD_FOLDER = str(BASE_DIR / 'app/utils/video/input')  # 上传视频路径

    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}  # 允许的视频格式
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

