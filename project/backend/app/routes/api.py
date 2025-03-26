# api.py
# 作用:定义API相关路由
# 当前状态：仅有一个测试接口/api/frames

import os
import re
import jwt
from functools import wraps
from werkzeug.utils import secure_filename
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify,request, g
from ..config import BaseConfig


api_bp = Blueprint('api', __name__)


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


@api_bp.route('/frames')
def get_frames():
    """获取所有帧数据接口"""
    frame_dir = os.path.join(BaseConfig.FRAME_FOLDER)

    try:
        files = sorted([
            f for f in os.listdir(frame_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])
    except FileNotFoundError:
        return jsonify({"error": "帧目录不存在"}), 404

    return jsonify({
        "total": len(files),
        "prefix": "/frame/",  # 与静态路由一致
        "files": files,
        "fps": 30
    })


@api_bp.route('/password_login', methods=['POST'])
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


@api_bp.route('/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get('phone')

    # 手机号格式验证
    if not re.match(r'^(?:(?:\+|00)86)?1[3-9]\d{9}$', phone):
        return jsonify({'success': False, 'message': '手机号格式错误'}), 400

    # 模拟发送验证码（正式环境需接入短信服务商API）
    print(f"模拟发送验证码至 {phone}: 123456")  # 控制台输出模拟验证码
    return jsonify({'success': True, 'message': '验证码已发送'})


@api_bp.route('/user-info', methods=['GET'])
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


@api_bp.route('/history', methods=['GET', 'DELETE'])
@jwt_required
def handle_history():
    global HISTORY_DATA

    if request.method == 'GET':
        try:
            return jsonify({
                "success": True,
                "data": HISTORY_DATA  # 确保返回结构包含 data 字段
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "获取历史记录失败"
            }), 500

    elif request.method == 'DELETE':
        data = request.get_json()
        item_id = data.get('id')

        # 校验 id 是否存在且有效
        if not item_id:
            return jsonify({
                "success": False,
                "message": "缺少参数 id"
            }), 400

        # 确保 id 是整数
        try:
            item_id = int(item_id)
        except ValueError:
            return jsonify({
                "success": False,
                "message": "无效的 id 格式"
            }), 400

        # 检查要删除的项是否存在
        original_length = len(HISTORY_DATA)
        HISTORY_DATA = [item for item in HISTORY_DATA if item['id'] != item_id]

        if len(HISTORY_DATA) == original_length:
            return jsonify({
                "success": False,
                "message": "未找到对应记录"
            }), 404

        return jsonify({
            "success": True,
            "message": "删除成功"
        })


# 添加模拟历史数据
HISTORY_DATA = [
    {
        "id": 1,
        "time": "2019-01-10 12:24:22",
        "status": "expired",
        "expiry": "2024-03-20",
        "report_url": "/assets/pdf/sample1.pdf"
    },
    {
        "id": 2,
        "time": "2024-1-20 12:24:22",
        "status": "processing",
        "expiry": "2024-03-20",
        "report_url": "/assets/pdf/sample1.pdf"
    },
    {
        "id": 3,
        "time": "2024-09-20 12:24:22",
        "status": "completed",
        "expiry": "2024-03-20",
        "report_url": "/assets/pdf/sample1.pdf"
    },
    # 其他数据...
]


@api_bp.route('/upload', methods=['POST'])
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