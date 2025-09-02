import os
import hashlib
import json
from datetime import datetime, timezone, timedelta
from flask import jsonify, request, Blueprint, current_app, send_from_directory
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

# 分片上传相关常量
CHUNK_UPLOAD_DIR = 'chunk_uploads'
UPLOAD_PROGRESS_FILE = 'upload_progress.json'


# 原有的单文件上传接口（保留兼容）
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
        relative_path = os.path.join(f"user_{user.user_id}", f"{video_id}{os.path.splitext(file.filename)[1]}").replace(
            "\\", "/")
        save_path = os.path.join(BaseConfig.UPLOAD_FOLDER, relative_path)

        # 保存文件到文件系统
        file.save(save_path)

        # 数据库事务操作
        try:
            # 创建视频记录
            new_video = UserVideo(
                video_id=video_id,
                user_id=user.user_id,
                video_path=relative_path
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

            # 异步任务处理
            process_video_async(
                input_path=save_path,
                filename=os.path.basename(save_path),
                original_video_id=video_id,
                user_id=user.user_id
            )

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


# 分片上传相关接口
@upload_bp.route('/upload/chunk', methods=['POST'])
@jwt_required
def upload_chunk():
    """上传单个分片 - 带详细参数验证日志"""
    try:
        # === 详细参数验证日志开始 ===
        current_app.logger.info("=== 分片上传参数验证开始 ===")
        
        # 打印所有请求参数
        current_app.logger.info(f"请求方法: {request.method}")
        current_app.logger.info(f"Content-Type: {request.headers.get('Content-Type', '未设置')}")
        current_app.logger.info(f"Content-Length: {request.headers.get('Content-Length', '未设置')}")
        
        # 打印所有表单参数
        current_app.logger.info("表单参数:")
        for key, value in request.form.items():
            current_app.logger.info(f"  {key}: {value}")
        
        # 打印所有文件参数
        current_app.logger.info("文件参数:")
        for key, file in request.files.items():
            if file:
                current_app.logger.info(f"  {key}: {file.filename} (大小: {len(file.read()) if file else 0} bytes)")
                file.seek(0)  # 重置文件指针
        
        # 打印请求头中的Authorization
        auth_header = request.headers.get('Authorization')
        current_app.logger.info(f"Authorization头: {'存在' if auth_header else '缺失'}")
        if auth_header:
            current_app.logger.info(f"  格式: {auth_header[:50]}...")
        
        # === 基础验证 ===
        if 'chunk' not in request.files:
            current_app.logger.error("❌ 缺少分片文件: 'chunk' 不在 request.files 中")
            current_app.logger.info(f"可用的文件键: {list(request.files.keys())}")
            return jsonify({"success": False, "message": "缺少分片文件"}), 400

        chunk = request.files['chunk']
        
        # 检查chunk参数
        required_params = ['index', 'totalChunks', 'hash', 'filename']
        missing_params = []
        param_values = {}
        
        for param in required_params:
            value = request.form.get(param)
            if value is None or value == '':
                missing_params.append(param)
            else:
                param_values[param] = value
        
        if missing_params:
            current_app.logger.error(f"❌ 缺少必需参数: {missing_params}")
            current_app.logger.info(f"已提供的参数: {param_values}")
            return jsonify({"success": False, "message": f"缺少参数: {missing_params}"}), 400
        
        try:
            index = int(request.form.get('index', 0))
            total_chunks = int(request.form.get('totalChunks', 1))
            hash_value = str(request.form.get('hash', ''))
            filename = str(request.form.get('filename', ''))
            
            current_app.logger.info(f"✅ 参数解析成功:")
            current_app.logger.info(f"  index: {index} (类型: {type(index)})")
            current_app.logger.info(f"  total_chunks: {total_chunks} (类型: {type(total_chunks)})")
            current_app.logger.info(f"  hash: {hash_value[:20]}... (长度: {len(hash_value)})")
            current_app.logger.info(f"  filename: {filename}")
            
        except ValueError as e:
            current_app.logger.error(f"❌ 参数格式错误: {str(e)}")
            current_app.logger.info(f"原始值 - index: {request.form.get('index')}, totalChunks: {request.form.get('totalChunks')}")
            return jsonify({"success": False, "message": f"参数格式错误: {str(e)}"}), 400

        # 验证文件
        if not chunk or chunk.filename == '':
            current_app.logger.error("❌ 上传的文件为空: chunk对象无效或文件名为空")
            current_app.logger.info(f"chunk对象: {chunk}, filename: {getattr(chunk, 'filename', 'N/A')}")
            return jsonify({"success": False, "message": "上传的文件为空"}), 400

        # 检查文件内容
        chunk.seek(0, os.SEEK_END)
        file_size = chunk.tell()
        chunk.seek(0)
        
        current_app.logger.info(f"📁 文件信息: {chunk.filename}, 大小: {file_size} bytes")

        if file_size == 0:
            current_app.logger.error("❌ 上传的文件为空: 文件大小为0字节")
            return jsonify({"success": False, "message": "上传的文件为空"}), 400

        # 验证文件名
        if not filename or filename.strip() == '':
            current_app.logger.error("❌ 缺少文件名: filename为空或仅包含空白字符")
            return jsonify({"success": False, "message": "缺少文件名"}), 400

        # === JWT认证 ===
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            current_app.logger.error("❌ 无效的认证头: Authorization头格式错误")
            current_app.logger.info(f"Authorization头内容: {auth_header}")
            return jsonify({"success": False, "message": "无效的认证头"}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
            user_phone = payload['phone']
            current_app.logger.info(f"✅ JWT解析成功: 用户手机号 {user_phone}")
        except Exception as e:
            current_app.logger.error(f"❌ JWT解析失败: {str(e)}")
            return jsonify({"success": False, "message": "JWT解析失败"}), 401

        user = User.query.filter_by(phone=user_phone).first()
        if not user:
            current_app.logger.error(f"❌ 用户不存在: 手机号 {user_phone}")
            return jsonify({"success": False, "message": "用户不存在"}), 404

        current_app.logger.info(f"✅ 用户验证成功: user_id={user.user_id}")

        # === 文件保存 ===
        # 创建分片上传临时目录
        file_hash = hashlib.md5(filename.encode()).hexdigest()
        temp_dir = os.path.join(
            BaseConfig.UPLOAD_FOLDER,
            CHUNK_UPLOAD_DIR,
            f"user_{user.user_id}",
            file_hash
        )
        
        current_app.logger.info(f"📂 临时目录: {temp_dir}")
        os.makedirs(temp_dir, exist_ok=True)

        # 保存分片
        chunk_filename = f"chunk_{index:06d}"
        chunk_path = os.path.join(temp_dir, chunk_filename)

        try:
            chunk.save(chunk_path)
            current_app.logger.info(f"✅ 分片保存成功: {chunk_path}")

            # 验证保存的文件
            if not os.path.exists(chunk_path):
                current_app.logger.error("❌ 文件保存失败: 文件不存在")
                return jsonify({"success": False, "message": "文件保存失败"}), 500
                
            saved_size = os.path.getsize(chunk_path)
            if saved_size != file_size:
                current_app.logger.error(f"❌ 文件大小不匹配: 期望{file_size}, 实际{saved_size}")
                return jsonify({"success": False, "message": "文件保存不完整"}), 500

            current_app.logger.info(f"✅ 文件验证通过: 大小{saved_size}字节")

        except Exception as e:
            current_app.logger.error(f"❌ 文件保存失败: {str(e)}")
            return jsonify({"success": False, "message": "文件保存失败"}), 500

        # 保存上传进度
        progress_file = os.path.join(temp_dir, UPLOAD_PROGRESS_FILE)
        progress = {"uploaded_chunks": [], "total_chunks": total_chunks, "filename": filename}

        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress = json.load(f)

        if index not in progress["uploaded_chunks"]:
            progress["uploaded_chunks"].append(index)
            progress["uploaded_chunks"].sort()

        with open(progress_file, 'w') as f:
            json.dump(progress, f)

        current_app.logger.info(f"✅ 进度更新成功: 已上传{len(progress['uploaded_chunks'])}/{total_chunks}个分片")
        current_app.logger.info("=== 分片上传完成 ===")

        return jsonify({
            "success": True,
            "message": "分片上传成功",
            "data": {
                "index": index,
                "uploaded": True,
                "size": file_size
            }
        }), 200

    except ValueError as e:
        current_app.logger.error(f"❌ 参数格式错误: {str(e)}")
        return jsonify({"success": False, "message": f"参数格式错误: {str(e)}"}), 400
    except Exception as e:
        current_app.logger.error(f"❌ 分片上传失败: {str(e)}")
        current_app.logger.error(f"异常类型: {type(e)}")
        return jsonify({
            "success": False,
            "message": "分片上传失败",
            "error": str(e)
        }), 500


@upload_bp.route('/upload/merge', methods=['POST'])
@jwt_required
def merge_chunks():
    """合并分片 - 修复版：基于实际文件检测"""
    try:
        data = request.get_json()
        filename = data.get('filename', '')
        total_chunks = data.get('totalChunks', 0)

        if not filename or total_chunks <= 0:
            return jsonify({"success": False, "message": "参数错误"}), 400

        # 解析 JWT
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "缺少认证"}), 401

        token = auth_header.split(' ')[1]
        payload = decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        user_phone = payload['phone']

        user = User.query.filter_by(phone=user_phone).first()
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 检查分片目录
        file_hash = hashlib.md5(filename.encode()).hexdigest()
        temp_dir = os.path.join(
            BaseConfig.UPLOAD_FOLDER,
            CHUNK_UPLOAD_DIR,
            f"user_{user.user_id}",
            file_hash
        )

        if not os.path.exists(temp_dir):
            return jsonify({"success": False, "message": "上传目录不存在"}), 400

        # **关键修复：直接扫描实际存在的分片文件**
        actual_chunks = []
        for i in range(total_chunks):
            chunk_path = os.path.join(temp_dir, f"chunk_{i:06d}")
            if os.path.exists(chunk_path):
                actual_chunks.append(i)
        
        current_app.logger.info(f"实际扫描到的分片: {actual_chunks}")
        
        # 基于实际文件进行验证
        expected_chunks = set(range(total_chunks))
        uploaded_chunks = set(actual_chunks)
        
        if len(uploaded_chunks) < total_chunks:
            missing = list(expected_chunks - uploaded_chunks)
            current_app.logger.warning(f"实际缺失分片: {missing}")
            
            return jsonify({
                "success": False,
                "message": "分片不完整",
                "uploaded": len(uploaded_chunks),
                "total": total_chunks,
                "missing": missing
            }), 400

        # 验证所有分片文件存在
        for i in range(total_chunks):
            chunk_path = os.path.join(temp_dir, f"chunk_{i:06d}")
            if not os.path.exists(chunk_path):
                current_app.logger.error(f"分片文件缺失: {chunk_path}")
                return jsonify({
                    "success": False,
                    "message": f"分片文件 {i} 不存在"
                }), 400

        # 生成视频ID并合并
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        video_id = f"{timestamp}"
        
        file_extension = os.path.splitext(filename)[1]
        relative_path = os.path.join(
            f"user_{user.user_id}",
            f"{video_id}{file_extension}"
        ).replace("\\", "/")
        final_path = os.path.join(BaseConfig.UPLOAD_FOLDER, relative_path)

        # 合并分片
        try:
            with open(final_path, 'wb') as final_file:
                total_size = 0
                for i in range(total_chunks):
                    chunk_path = os.path.join(temp_dir, f"chunk_{i:06d}")
                    with open(chunk_path, 'rb') as chunk_file:
                        data = chunk_file.read()
                        final_file.write(data)
                        total_size += len(data)

            current_app.logger.info(f"合并成功: {final_path} ({total_size} bytes)")
        except Exception as e:
            current_app.logger.error(f"合并失败: {str(e)}")
            return jsonify({"success": False, "message": "合并失败"}), 500

        # 清理临时文件
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

        # 数据库操作
        try:
            # 创建视频记录
            new_video = UserVideo(
                video_id=video_id,
                user_id=user.user_id,
                video_path=relative_path
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

            # 启动异步处理
            process_video_async(
                input_path=final_path,
                filename=os.path.basename(final_path),
                original_video_id=video_id,
                user_id=user.user_id
            )

        except Exception as e:
            db.session.rollback()
            # 回滚文件操作
            if os.path.exists(final_path):
                os.remove(final_path)
            current_app.logger.error(f"数据库操作失败: {str(e)}")
            raise e

        return jsonify({
            "success": True,
            "message": "文件合并成功",
            "data": {
                "video_id": video_id,
                "history_id": new_history.history_id,
                "status_url": f"/api/status/{video_id}"
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"合并分片失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": "合并分片失败",
            "error": str(e)
        }), 500


@upload_bp.route('/upload/status', methods=['POST'])
@jwt_required
def check_upload_status():
    """检查断点续传状态 - 增强版"""
    try:
        data = request.get_json()
        filename = data.get('filename', '')
        size = data.get('size', 0)

        if not filename:
            return jsonify({"success": False, "message": "缺少文件名"}), 400

        # 解析 JWT 获取用户信息
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "缺少或无效的认证头"}), 401

        token = auth_header.split(' ')[1]
        payload = decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        user_phone = payload['phone']

        user = User.query.filter_by(phone=user_phone).first()
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 检查上传进度
        file_hash = hashlib.md5(filename.encode()).hexdigest()
        temp_dir = os.path.join(
            BaseConfig.UPLOAD_FOLDER,
            CHUNK_UPLOAD_DIR,
            f"user_{user.user_id}",
            file_hash
        )

        progress_file = os.path.join(temp_dir, UPLOAD_PROGRESS_FILE)

        if not os.path.exists(progress_file):
            return jsonify({
                "success": True,
                "uploadedChunks": [],
                "canResume": False,
                "totalChunks": 0,
                "filename": filename
            }), 200

        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            current_app.logger.warning(f"读取进度文件失败: {str(e)}")
            return jsonify({
                "success": True,
                "uploadedChunks": [],
                "canResume": False,
                "totalChunks": 0,
                "filename": filename
            }), 200

        return jsonify({
            "success": True,
            "uploadedChunks": progress.get("uploaded_chunks", []),
            "canResume": True,
            "totalChunks": progress.get("total_chunks", 0),
            "filename": progress.get("filename", filename)
        }), 200

    except Exception as e:
        current_app.logger.error(f"检查上传状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": "检查上传状态失败",
            "error": str(e)
        }), 500