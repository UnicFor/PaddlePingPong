import os
import subprocess
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from ..utils.models import db, UserVideoProcess, VideoFramesProcess, VideoFramesPose, VideoStatus, History

from .security import async_task
from ..config import BaseConfig

@async_task
def process_video_async(input_path, filename, original_video_id, user_id):
    """⚡ 异步处理视频的函数（使用ORM版本）"""
    try:
        # ================== 路径配置 ==================
        # 配置中心化的路径常量, 创建用户专属目录结构

        # 处理后的视频目录
        processed_user_dir = Path(BaseConfig.PROCESSED_FOLDER) / f"user_{user_id}"
        processed_user_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(processed_user_dir / filename)

        # 骨骼视频目录
        pose_user_dir = Path(BaseConfig.POSE_FOLDER) / f"user_{user_id}"
        pose_user_dir.mkdir(parents=True, exist_ok=True)
        pose_video_path = str(pose_user_dir / filename)

        # 帧存储目录
        frames_user_dir = Path(BaseConfig.FRAMES_FOLDER) / f"user_{user_id}"
        frames_user_dir.mkdir(parents=True, exist_ok=True)

        # 原始视频帧目录
        frame_output_dir = frames_user_dir / filename.split('.')[0]
        frame_output_dir.mkdir(parents=True, exist_ok=True)

        # 骨骼视频帧目录
        pose_frame_dir = frames_user_dir / f"{filename.split('.')[0]}_pose"
        pose_frame_dir.mkdir(parents=True, exist_ok=True)

        # ================== 视频处理阶段 ==================
        print(f"\n🔵 开始处理视频: {filename} (ID: {original_video_id})")

        # 调用检测脚本（保持原逻辑）
        cmd = [
            'python', 'project/backend/app/utils/balldetect_pos_vel/ball_detect.py',
            '--model_path', 'project/backend/app/utils/balldetect_pos_vel/ball_detect.pt',
            '--video_path', input_path,
            '--video_out_path', output_path
        ]
        print(f"⚙️ 正在运行检测脚本: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if result.returncode != 0:
            print(f"❌ 处理失败: {result.stderr}")
            return
        print(f"✅ 视频处理完成: {output_path}")

        # ================== 数据库写入阶段 ==================
        # 使用ORM代替原始SQL
        processed_video_id = f"{original_video_id.split('_')[-1]}"
        try:
            print(f"📝 写入处理视频记录: {processed_video_id}")
            # ORM对象创建
            processed_video = UserVideoProcess(
                video_id=processed_video_id,
                user_id=user_id,
                video_path_process=output_path
            )
            db.session.add(processed_video)
            db.session.commit()

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"❌ 数据库错误: {e}")

        # ================== 帧处理阶段 ==================
        # 帧提取（保持原逻辑）
        frame_script = [
            'python', 'project/backend/app/utils/balldetect_pos_vel/video2frame.py',
            '--video_path', output_path,
            '--output_dir', str(frame_output_dir),
            '--frame_interval', '1'
        ]
        print(f"🖼️ 开始提取帧到目录: {frame_output_dir}")
        frame_result = subprocess.run(frame_script, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if frame_result.returncode != 0:
            print(f"❌ 帧提取失败: {frame_result.stderr}")
            return
        frame_files = sorted(os.listdir(frame_output_dir))
        print(f"✅ 帧提取完成，共 {len(frame_files)} 帧")

        # 批量写入帧记录（ORM优化）
        try:
            print(f"📋 开始写入 {len(frame_files)} 条帧记录...")
            frames = [
                VideoFramesProcess(
                    frame_id=f"{original_video_id}_{idx}",
                    video_id=original_video_id,
                    frame_index=idx,
                    frame_path_process=str(frame_output_dir / frame_file)
                )
                for idx, frame_file in enumerate(frame_files, 1)
            ]
            db.session.bulk_save_objects(frames)
            db.session.commit()

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"❌ 帧记录错误: {e}")

        # ================== 骨骼检测阶段 ==================
        print(f"🧍 开始人体骨骼检测: {filename}")
        pose_cmd = [
            'python', 'project/backend/app/utils/mmpose/predict.py',
            'project/backend/app/utils/mmpose/utils/coco_person.py',
            'project/backend/app/utils/mmpose/utils/model1.pth',
            'project/backend/app/utils/mmpose/utils/config.py',
            'project/backend/app/utils/mmpose/utils/model2.pth',
            '--input', output_path,
            '--output-root', pose_video_path,
            '--device', 'cuda:0',
            '--save-predictions'
        ]
        print(f"⚙️ 正在运行骨骼检测脚本: {' '.join(pose_cmd)}")
        pose_result = subprocess.run(pose_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if pose_result.returncode != 0:
            print(f"❌ 骨骼检测失败: {pose_result.stderr}")
        else:
            # 骨骼帧处理（ORM批量操作）
            pose_frame_script = [
                'python', 'mmpose/video2frame.py',
                '--video_path', pose_video_path,
                '--output_dir', str(pose_frame_dir),
                '--frame_interval', '1'
            ]
            print(f"🖼️ 开始提取骨骼帧到目录: {pose_frame_dir}")
            pose_frame_result = subprocess.run(pose_frame_script, capture_output=True, text=True, encoding='utf-8',
                                               errors='ignore')

            if pose_frame_result.returncode == 0:
                pose_frame_files = sorted(os.listdir(pose_frame_dir))
                try:
                    print(f"📋 开始写入 {len(pose_frame_files)} 条骨骼帧记录...")
                    pose_frames = [
                        VideoFramesPose(
                            frame_id=f"{original_video_id}_{idx}",
                            video_id=original_video_id,
                            frame_index=idx,
                            frame_path=str(pose_frame_dir / frame_file)
                        )
                        for idx, frame_file in enumerate(pose_frame_files, 1)
                    ]
                    db.session.bulk_save_objects(pose_frames)
                    db.session.commit()
                except SQLAlchemyError as e:
                    db.session.rollback()
                    print(f"❌ 骨骼帧记录错误: {e}")

        # ================== 状态更新阶段 ==================
        try:
            video_status = VideoStatus.query.filter_by(video_id=original_video_id).first()
            if video_status:
                video_status.status = 3

            history_entry = History.query.filter_by(video_id=original_video_id).first()
            if history_entry:
                history_entry.status = "completed"  # 使用您在模型中定义的状态值
                db.session.commit()
                print(f"✅ 状态更新为已完成")


        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"❌ 状态更新错误: {e}")

    except Exception as e:
        print(f"❌ 异步处理异常: {e}")
    finally:
        db.session.close()
        print(f"🏁 处理任务结束: {filename}\n")