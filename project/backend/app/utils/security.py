from functools import wraps
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta, timezone
from flask import jsonify, g, request
from ..config import BaseConfig


def jwt_required(f):
    """JWT验证装饰器"""
    @wraps(f)
    def decorated_function(*args,  ** kwargs):
        # 认证头校验
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "message": "需要提供有效令牌"
            }), 401

        # 提取并验证令牌
        token = auth_header.split(' ')[1]
        try:
            payload = decode(
                token,
                BaseConfig.SECRET_KEY,
                algorithms=["HS256"]
            )
            g.user_phone = payload['phone']
        except ExpiredSignatureError:
            return jsonify({
                "success": False,
                "message": "会话已过期"
            }), 401
        except InvalidTokenError:
            return jsonify({
                "success": False,
                "message": "无效令牌"
            }), 401
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "认证失败"
            }), 401

        return f(*args, ** kwargs)
    return decorated_function