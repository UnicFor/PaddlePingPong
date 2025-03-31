from functools import wraps
import jwt
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta, timezone
from flask import jsonify, g, request
from ..config import BaseConfig
from ..utils.models import User  # 导入用户模型
from ..extensions import db  # 导入数据库实例


def jwt_required(f):
    """增强版JWT验证装饰器
    功能：
    1. 验证请求头中的Bearer Token
    2. 解析并验证JWT有效性
    3. 查询数据库验证用户存在性
    4. 注入用户对象到上下文
    """

    @wraps(f)
    def decorated_function(*args, ** kwargs):
        auth_header = request.headers.get('Authorization')
        print(f"\n===== 开始验证请求 =====")
        print(f"请求路径: {request.path}")
        print(f"请求头: {auth_header}")

        # 验证头格式
        if not auth_header or not auth_header.startswith('Bearer '):
            print("!! 错误：Authorization头格式错误")
            return jsonify({"success": False, "message": "需要提供有效的Bearer令牌"}), 401

        token = auth_header.split(' ')[1]
        print(f"提取的令牌: {token[:10]}... (长度: {len(token)})")

        try:
            # 解码验证
            payload = decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
            print(f"解码后的载荷: {payload}")

            # 用户查询
            user = User.query.get(payload['user_id'])
            print(f"数据库查询结果: {user}")

            if not user:
                print("!! 错误：用户不存在")
                return jsonify({"success": False, "message": "用户不存在"}), 404

            g.current_user = user
            print("===== 验证通过 =====")

        except ExpiredSignatureError:
            print("!! 错误：令牌过期")
            return jsonify({"success": False, "message": "会话已过期"}), 401
        except InvalidTokenError as e:
            print(f"!! 令牌无效: {str(e)}")
            return jsonify({"success": False, "message": f"无效令牌: {str(e)}"}), 401
        except Exception as e:
            print(f"!! 服务器错误: {str(e)}")
            return jsonify({"success": False, "message": "服务器验证错误"}), 500

        return f(*args, ** kwargs)
    return decorated_function


def generate_token(user):
    payload = {
        'user_id': user.user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=2),
        'iat': datetime.now(timezone.utc)
    }

    token = jwt.encode(
        payload=payload,
        key=BaseConfig.SECRET_KEY,
        algorithm="HS256"
    )

    return token