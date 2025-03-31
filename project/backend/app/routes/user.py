from flask import jsonify, Blueprint, g
from ..utils.security import jwt_required
from ..utils.models import User

user_bp = Blueprint('user', __name__)


@user_bp.route('/user-info', methods=['GET'])
@jwt_required
def get_user_info():
    """获取当前用户信息（数据库版本）"""
    try:
        # 从JWT中获取当前用户
        current_user = g.current_user

        # 数据库查询
        user = User.query.get(current_user.user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "用户不存在"
            }), 404

        return jsonify({
            "success": True,
            "data": user.to_dict()
        })

    except Exception as e:
        print(f"用户信息查询失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500