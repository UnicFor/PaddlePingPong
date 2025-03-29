import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import jsonify, request, Blueprint
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from ..config import BaseConfig
from ..utils.security import jwt_required

from .history import HISTORY_DATA  # 导入共享历史数据

upload_bp = Blueprint('upload', __name__)

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

        # 从JWT获取用户信息（根据现有登录接口结构）
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        payload = decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        user_phone = payload['phone']  # 假设使用手机号作为用户标识

        # 创建用户专属目录（使用手机号哈希作为目录名）
        user_folder = os.path.join(BaseConfig.UPLOAD_FOLDER, f"user_{hash(user_phone)}")
        os.makedirs(user_folder, exist_ok=True)

        # 生成安全文件名
        filename = secure_filename(file.filename)
        unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        save_path = os.path.join(user_folder, unique_name)

        # 保存文件
        file.save(save_path)

        # 更新历史记录（使用现有HISTORY_DATA结构）
        new_history = {
            "id": len(HISTORY_DATA) + 1,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "completed",
            "file_path": save_path,
            "filename": filename
        }
        HISTORY_DATA.append(new_history)

        return jsonify({
            "success": True,
            "message": "上传成功",
            "data": {
                "path": save_path,
                "preview_url": f"/uploads/{os.path.basename(user_folder)}/{unique_name}"
            }
        }), 200

    except ExpiredSignatureError:
        return jsonify({"success": False, "message": "会话已过期"}), 401
    except InvalidTokenError:
        return jsonify({"success": False, "message": "无效令牌"}), 401
    except Exception as e:
        print(f"上传失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": "文件保存失败",
            "error": str(e)
        }), 500