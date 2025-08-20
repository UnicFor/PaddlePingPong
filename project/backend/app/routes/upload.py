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
    """上传单个分片"""
    try:
        # 基础验证
        if 'chunk' not in request.files:
            return jsonify({"success": False, "message": "缺少分片文件"}), 400

        chunk = request.files['chunk']
        index = int(request.form.get('index', 0))
        total_chunks = int(request.form.get('totalChunks', 1))
        hash_value = request.form.get('hash', '')
        filename = request.form.get('filename', '')

        # 关键验证：检查文件是否为空
        if not chunk or chunk.filename == '':
            return jsonify({"success": False, "message": "上传的文件为空"}), 400

        # 检查文件内容
        chunk.seek(0, os.SEEK_END)
        file_size = chunk.tell()
        chunk.seek(0)  # 重置文件指针

        if file_size == 0:
            return jsonify({"success": False, "message": "上传的文件为空"}), 400

        if not filename:
            return jsonify({"success": False, "message": "缺少文件名"}), 400

        # 解析 JWT 获取用户信息
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "无效的认证头"}), 401

        token = auth_header.split(' ')[1]
        payload = decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        user_phone = payload['phone']

        user = User.query.filter_by(phone=user_phone).first()
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 创建分片上传临时目录
        temp_dir = os.path.join(
            BaseConfig.UPLOAD_FOLDER,
            CHUNK_UPLOAD_DIR,
            f"user_{user.user_id}",
            hashlib.md5(filename.encode()).hexdigest()
        )
        os.makedirs(temp_dir, exist_ok=True)

        # 保存分片
        chunk_filename = f"chunk_{index:06d}"
        chunk_path = os.path.join(temp_dir, chunk_filename)

        try:
            chunk.save(chunk_path)

            # 验证保存的文件
            if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
                return jsonify({"success": False, "message": "文件保存失败"}), 500

        except Exception as e:
            current_app.logger.error(f"文件保存失败: {str(e)}")
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
        current_app.logger.error(f"参数格式错误: {str(e)}")
        return jsonify({"success": False, "message": "参数格式错误"}), 400
    except Exception as e:
        current_app.logger.error(f"分片上传失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": "分片上传失败",
            "error": str(e)
        }), 500


@upload_bp.route('/upload/merge', methods=['POST'])
@jwt_required
def merge_chunks():
    """合并分片 - 增强修复版"""
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

        # 读取进度文件
        progress_file = os.path.join(temp_dir, UPLOAD_PROGRESS_FILE)
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
        except:
            return jsonify({"success": False, "message": "无法读取上传进度"}), 400

        # 关键修复：允许部分缺失并记录详细日志
        expected_chunks = set(range(total_chunks))
        uploaded_chunks = set(progress.get("uploaded_chunks", []))
        
        # 记录详细信息
        current_app.logger.info(f"合并检查: 期望{total_chunks}个, 已上传{len(uploaded_chunks)}个")
        
        if len(uploaded_chunks) < total_chunks:
            missing = list(expected_chunks - uploaded_chunks)
            current_app.logger.warning(f"缺失分片: {missing}")
            
            # 关键修复：允许继续合并（可选）
            if len(uploaded_chunks) >= total_chunks * 0.8:  # 80%完成度
                current_app.logger.warning("分片不完整但继续合并")
            else:
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
            # process_video_async(
            #     input_path=final_path,
            #     filename=os.path.basename(final_path),
            #     original_video_id=video_id,
            #     user_id=user.user_id
            # )

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