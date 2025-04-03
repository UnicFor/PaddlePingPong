# video.py
from flask import Blueprint, jsonify, url_for, g, send_from_directory, current_app
from ..utils.models import User, UserVideo, UserVideoProcess
from ..utils.security import jwt_required
from ..config import BaseConfig

video_bp = Blueprint('video', __name__)

@video_bp.route('/video/<string:video_id>', methods=['GET'])
@jwt_required
def get_video_urls(video_id):
    """获取视频地址接口"""
    try:
        current_user = g.current_user
        user = User.query.get(current_user.user_id)
        if not user:
            return jsonify(success=False, message="用户不存在"), 404

        original = UserVideo.query.filter_by(
            video_id=video_id, user_id=user.user_id
        ).first()
        processed = UserVideoProcess.query.filter_by(
            video_id=video_id, user_id=user.user_id
        ).first()

        if not original:
            return jsonify(success=False, message="视频不存在"), 404

        # 动态构建路径（确保使用正斜杠）
        original_filename = f"input/{original.video_path}"
        processed_filename = (
            f"output_pose/{processed.video_path_process}"
            if processed else None
        )

        return jsonify(success=True, data={
            "original": url_for('video.get_video', filename=original_filename, _external=True),
            "processed": url_for('video.get_video', filename=processed_filename, _external=True) if processed else None
        })

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500


@video_bp.route('/get_video/<path:filename>')
def get_video(filename):
    """最简单的文件访问路由"""
    return send_from_directory(BaseConfig.UTILS_FOLDER, filename)