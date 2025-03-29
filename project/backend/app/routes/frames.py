import os
from flask import jsonify, Blueprint
from ..config import BaseConfig

frames_bp = Blueprint('frames', __name__)

@frames_bp.route('/frames')
def get_frames():
    """获取所有帧数据接口"""
    frame_dir = os.path.join(BaseConfig.FRAME_FOLDER)

    try:
        files = sorted([
            f for f in os.listdir(frame_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])
    except FileNotFoundError:
        return jsonify({"error": "帧目录不存在"}), 404

    return jsonify({
        "total": len(files),
        "prefix": "/frame/",  # 与静态路由一致
        "files": files,
        "fps": 30
    })