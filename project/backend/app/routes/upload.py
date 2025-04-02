import os
from datetime import datetime, timezone, timedelta
from flask import jsonify, request, Blueprint, current_app
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from ..extensions import db
from ..utils.models import User, UserVideo, History, VideoStatus
from ..config import BaseConfig
from ..utils.security import jwt_required

from ..utils.task import process_video_async

upload_bp = Blueprint('upload', __name__)

# 状态常量
VIDEO_STATUS_UPLOADED = 1
HISTORY_STATUS_UPLOADED = "processing"




@upload_bp.route('/upload', methods=['POST'])
@jwt_required
def upload_video():
    try:
        # 基础验证
        if 'video' not in request.files:
            return jsonify({"success": False, "message": "请选择视频文件"}), 400

        file = request.files['video']
        if file.filename == '':
            return jsonify({"success": False, "message": "无效文件名"}), 400

        # 解析 JWT
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        payload = decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        user_phone = payload['phone']

        # 查询用户信息
        user = User.query.filter_by(phone=user_phone).first()
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 生成唯一视频ID（时间戳）
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        video_id = f"{timestamp}"

        # 创建用户专属目录
        user_folder = os.path.join(BaseConfig.UPLOAD_FOLDER, f"user_{user.user_id}")
        os.makedirs(user_folder, exist_ok=True)

        # 构建保存路径
        save_path = os.path.join(user_folder, f"{video_id}{os.path.splitext(file.filename)[1]}")

        # 保存文件到文件系统
        file.save(save_path)

        # 数据库事务操作
        try:
            # 创建视频记录
            new_video = UserVideo(
                video_id=video_id,
                user_id=user.user_id,
                video_path=save_path
            )
            db.session.add(new_video)

            # 创建视频状态记录
            video_status = VideoStatus(
                video_id=video_id,
                status=VIDEO_STATUS_UPLOADED
            )
            db.session.add(video_status)

            db.session.flush()

            # 创建历史记录
            new_history = History(
                user_id=user.user_id,
                video_id=video_id,
                create_time=datetime.now(),
                status=HISTORY_STATUS_UPLOADED,
                expiry=datetime.now(timezone.utc) + timedelta(days=7)
            )
            db.session.add(new_history)
            db.session.commit()

            process_video_async(
                input_path=save_path,
                filename=os.path.basename(save_path),
                original_video_id=video_id,
                user_id=user.user_id
            )

        # 异步任务处理
        except Exception as e:
            db.session.rollback()
            # 回滚文件操作
            if os.path.exists(save_path):
                os.remove(save_path)
            current_app.logger.error(f"数据库操作失败: {str(e)}")
            raise e

        return jsonify({
            "success": True,
            "message": "上传成功",
            "data": {
                "video_id": video_id,
                "history_id": new_history.history_id,
                "status_url": f"/api/status/{video_id}"
            }
        }), 200

    except ExpiredSignatureError:
        return jsonify({"success": False, "message": "会话已过期"}), 401
    except InvalidTokenError:
        return jsonify({"success": False, "message": "无效令牌"}), 401
    except Exception as e:
        current_app.logger.error(f"上传失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": "文件处理失败",
            "error": str(e)
        }), 500