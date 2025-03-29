from flask import jsonify, Blueprint
from ..utils.security import jwt_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/user-info', methods=['GET'])
@jwt_required
def get_user_info():
    """获取当前用户信息接口"""
    try:
        # 模拟数据库查询 - 正式环境替换为真实查询
        user_data = {
            "phone":13812345678,
            "weixin":"",
            "username":"adQd12DAsd1",
            "registration_date": "2023-01-01",
            "user_role": "member"
        }

        return jsonify({
            "success": True,
            "data": user_data
        })

    except Exception as e:
        print(f"用户信息查询失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500