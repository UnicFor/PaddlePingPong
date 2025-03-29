import re
import jwt
from datetime import datetime, timedelta, timezone
from flask import jsonify, request, Blueprint
from ..config import BaseConfig

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/password_login', methods=['POST'])
def login():
    """登录验证接口"""
    data = request.get_json()

    # 基础参数校验
    if not data or 'phone' not in data or 'type' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400

    phone = data['phone']
    login_type = data['type']

    # 手机号格式验证
    if not re.match(r'^(?:(?:\+|00)86)?1[3-9]\d{9}$', phone):
        return jsonify({'success': False, 'message': '手机号格式错误'}), 400

    # 密码登录分支
    if login_type == 'password':
        if 'password' not in data:
            return jsonify({'success': False, 'message': '缺少密码参数'}), 400

        # 正式环境需要替换为数据库查询
        if phone == "13812345678" and data['password'] == "password123":
            # 生成JWT（有效2小时）
            token = jwt.encode({
                'phone': phone,
                'exp': datetime.now(timezone.utc) + timedelta(hours=2)
            }, BaseConfig.SECRET_KEY, algorithm="HS256")

            return jsonify({
                'success': True,
                'message': '登录成功',
                'token': token
            }), 200
        else:
            return jsonify({'success': False, 'message': '手机号或密码错误'}), 401

    # 验证码登录逻辑
    elif login_type == 'sms':
        if 'sms_code' not in data:
            return jsonify({'success': False, 'message': '缺少验证码参数'}), 400

        # 模拟验证码验证（正式环境需查询缓存）
        if data['sms_code'] == "123456":
            token = jwt.encode({
                'phone': phone,
                'exp': datetime.now(timezone.utc) + timedelta(hours=2)
            }, BaseConfig.SECRET_KEY, algorithm="HS256")

            return jsonify({
                'success': True,
                'message': '登录成功',
                'token': token
            }), 200
        else:
            return jsonify({'success': False, 'message': '验证码错误'}), 401
    else:
        return jsonify({'success': False, 'message': '无效的登录类型'}), 400


@auth_bp.route('/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get('phone')

    # 手机号格式验证
    if not re.match(r'^(?:(?:\+|00)86)?1[3-9]\d{9}$', phone):
        return jsonify({'success': False, 'message': '手机号格式错误'}), 400

    # 模拟发送验证码（正式环境需接入短信服务商API）
    print(f"模拟发送验证码至 {phone}: 123456")  # 控制台输出模拟验证码
    return jsonify({'success': True, 'message': '验证码已发送'})
