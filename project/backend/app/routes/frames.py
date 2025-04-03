import base64
import os
from flask import Blueprint, jsonify, url_for, g, send_from_directory
from ..utils.models import User, UserVideo
from ..utils.security import jwt_required
from ..config import BaseConfig

frames_bp = Blueprint('frames', __name__)

@frames_bp.route('/frames-batch/<string:video_id>')
@jwt_required
def get_frames_batch(video_id):
    """批量获取帧数据（Base64编码）"""
    try:
        current_user = g.current_user
        user = User.query.get(current_user.user_id)
        if not user:
            return jsonify(success=False, message="用户不存在"), 404

        video = UserVideo.query.filter_by(
            video_id=video_id,
            user_id=user.user_id
        ).first()
        if not video:
            return jsonify(success=False, message="无权访问"), 403

        user_dir = f"user_{user.user_id}"
        frame_dir = os.path.join(
            BaseConfig.FRAMES_FOLDER,
            user_dir,
            video_id
        )

        files = sorted([
            f for f in os.listdir(frame_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])

        # 批量读取并编码图片
        frame_data = []
        for filename in files:
            filepath = os.path.join(frame_dir, filename)
            with open(filepath, "rb") as img_file:
                # 根据实际图片类型修改MIME类型
                mime_type = 'image/jpeg' if filename.lower().endswith('.jpg') else 'image/png'
                base64_data = base64.b64encode(img_file.read()).decode('utf-8')
                frame_data.append(f"data:{mime_type};base64,{base64_data}")

        return jsonify({
            "success": True,
            "data": {
                "total": len(files),
                "frames": frame_data
            }
        })

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500