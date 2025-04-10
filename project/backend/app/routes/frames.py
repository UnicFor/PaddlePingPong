import base64
import os
from flask import Blueprint, jsonify, g, json, Response
from json.decoder import JSONDecodeError
from ..utils.models import User, UserVideo
from ..utils.security import jwt_required
from ..config import BaseConfig

frames_bp = Blueprint('frames', __name__)

def convert_ndarray(obj):
    if isinstance(obj, dict):
        if '__ndarray__' in obj:
            return obj['__ndarray__']
        return {k: convert_ndarray(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarray(item) for item in obj]
    return obj

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


@frames_bp.route('/pose-frames/<string:video_id>')
@jwt_required
def get_pose_frames(video_id):
    """获取处理后的骨骼帧（Base64编码）"""
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

        # 骨骼帧存储路径规则
        user_dir = f"user_{user.user_id}"
        frame_dir = os.path.join(
            BaseConfig.FRAMES_FOLDER,
            user_dir,
            f"{video_id}_pose"  # 骨骼帧专用目录
        )

        if not os.path.exists(frame_dir):
            return jsonify(success=False, message="未找到骨骼帧数据"), 404

        files = sorted([
            f for f in os.listdir(frame_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])

        frame_data = []
        for filename in files:
            filepath = os.path.join(frame_dir, filename)
            with open(filepath, "rb") as img_file:
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


@frames_bp.route('/pose-data/<string:video_id>')
@jwt_required
def get_pose_data(video_id):
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
        pose_data_path = os.path.join(
            BaseConfig.POSE_FOLDER,
            user_dir,
            f"results_{video_id}.json"
        )

        if not os.path.exists(pose_data_path):
            return jsonify(success=False, message="未找到骨骼数据"), 404

        with open(pose_data_path, 'r') as f:
            raw_data = json.load(f)

            # 深度转换数据结构
            converted_data = {
                'meta_info': convert_ndarray(raw_data.get('meta_info', {})),
                'instance_info': [
                    {
                        'frame_id': frame.get('frame_id'),
                        'instances': [
                            {
                                'bbox': convert_ndarray(inst.get('bbox', [])),
                                'keypoints': convert_ndarray(inst.get('keypoints', [])),
                                'keypoint_scores': convert_ndarray(inst.get('keypoint_scores', []))
                            }
                            for inst in frame.get('instances', [])
                        ]
                    }
                    for frame in raw_data.get('instance_info', [])
                ]
            }

            return jsonify({
                "success": True,
                "data": converted_data
            })

    except JSONDecodeError:
        return jsonify(success=False, message="骨骼数据格式错误"), 500
    except Exception as e:
        return jsonify(success=False, message="服务器内部错误"), 500


@frames_bp.route('/ball-data/<string:video_id>')
@jwt_required
def get_ball_data(video_id):
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

        csv_path = os.path.join(
            BaseConfig.UTILS_FOLDER,
            "other",
            f"{video_id}_ball.csv"
        )

        if not os.path.exists(csv_path):
            return jsonify(success=False, message="未找到轨迹数据"), 404

        with open(csv_path, 'r') as f:
            csv_data = f.read()

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={video_id}_ball.csv"}
        )

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500