import shutil
from pathlib import Path
from flask import jsonify, request, Blueprint, g, current_app
from ..config import BaseConfig
from ..utils.security import jwt_required
from ..utils.models import History, UserVideo, VideoFramesProcess, VideoFramesPose, UserVideoProcess
from ..extensions import db

history_bp = Blueprint('history', __name__)

@history_bp.route('/history', methods=['GET'])
@jwt_required
def handle_history():
    current_user = g.current_user

    if request.method == 'GET':
        try:
            records = History.query.filter_by(user_id=current_user.user_id).all()
            return jsonify({
                "success": True,
                "data": [record.to_dict() for record in records]
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "获取历史记录失败"
            }), 500


@history_bp.route('/history/<int:history_id>', methods=['DELETE'])
@jwt_required
def delete_history(history_id):
    try:
        current_user = g.current_user
        current_user_id = current_user.user_id

        # 查询要删除的历史记录
        record = History.query.filter(
            History.history_id == history_id,
            History.user_id == current_user_id
        ).first()
        if not record:
            return jsonify({"success": False, "message": "记录不存在"}), 404

        video_id = record.video_id

        # 获取文件信息（在事务开始前）
        user_video = UserVideo.query.filter_by(video_id=video_id).first()
        if not user_video:
            return jsonify({"success": False, "message": "视频文件记录不存在"}), 404

        # 解析原始文件名
        original_path = Path(user_video.video_path)
        filename = original_path.name
        stem_name = original_path.stem

        # 构建所有相关路径
        user_dir = f"user_{current_user_id}"
        file_paths = {
            'original': Path(BaseConfig.UPLOAD_FOLDER) / user_dir / filename,
            'processed': Path(BaseConfig.PROCESSED_FOLDER) / user_dir / filename,
            'pose_video': Path(BaseConfig.POSE_FOLDER) / user_dir / filename,
            'pose_json': Path(BaseConfig.POSE_FOLDER) / user_dir / f"results_{stem_name}.json",
            'pose_md': Path(BaseConfig.POSE_FOLDER) / user_dir / f"results_{stem_name}.md",
            'frames_dir': Path(BaseConfig.FRAMES_FOLDER) / user_dir / stem_name,
            'pose_frames_dir': Path(BaseConfig.FRAMES_FOLDER) / user_dir / f"{stem_name}_pose",
            'other': Path(BaseConfig.UTILS_FOLDER) / f"other" / f"{stem_name}_ball.csv",
            'result': Path(BaseConfig.RESULT_FOLDER) / user_dir / f"{stem_name}.csv"

        }

        # 事务操作
        with db.session.begin_nested():
            # 删除关联记录
            db.session.delete(record)
            if video_id:
                UserVideo.query.filter_by(video_id=video_id).delete()
                VideoFramesProcess.query.filter_by(video_id=video_id).delete()
                VideoFramesPose.query.filter_by(video_id=video_id).delete()
                UserVideoProcess.query.filter_by(video_id=video_id).delete()

        db.session.commit()

        # 安全删除文件
        def safe_delete(path: Path):
            try:
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
                        current_app.logger.info(f"Deleted directory: {path}")
                    else:
                        path.unlink(missing_ok=True)
                        current_app.logger.info(f"Deleted file: {path}")
            except Exception as e:
                current_app.logger.error(f"删除失败 {path}: {str(e)}")

        # 执行删除操作
        for path in file_paths.values():
            safe_delete(path)

        return jsonify({"success": True, "message": "删除成功"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除失败[history_id={history_id}]: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "服务器处理删除请求时出错"}), 500


# 在history路由蓝图中添加

@history_bp.route('/history/<int:history_id>', methods=['GET'])
@jwt_required
def get_history_detail(history_id):
    current_user = g.current_user

    record = History.query.filter_by(
        history_id=history_id,
        user_id=current_user.user_id
    ).first()

    if not record:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    # 获取原始视频信息
    original_video = UserVideo.query.filter_by(
        video_id=record.video_id
    ).first()

    # 获取处理后的视频信息
    processed_video = UserVideoProcess.query.filter_by(
        video_id=record.video_id
    ).first()

    # 生成视频访问URL
    def generate_video_url(path):
        return f"/api/media/{current_user.user_id}/{Path(path).name}"

    return jsonify({
        "success": True,
        "data": {
            "original_video": generate_video_url(original_video.video_path),
            "processed_video": generate_video_url(processed_video.video_path_process),
            "frames": [
                {
                    "index": frame.frame_index,
                    "pose_frame": f"/api/media/{current_user.user_id}/{Path(frame.frame_path).name}",
                    "processed_frame": f"/api/media/{current_user.user_id}/{Path(frame.frame_path_process).name}"
                }
                for frame in original_video.pose_frames
            ]
        }
    })