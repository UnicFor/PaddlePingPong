import os
import subprocess
import pymysql

def process_video_async(input_path, filename, original_video_id, user_id, mysql_config):
    """⚡ 异步处理视频的函数 """
    try:
        # [监控点1] 开始处理视频
        print(f"\n🔵 开始处理视频: {filename} (ID: {original_video_id})")

        # 处理视频
        output_path = os.path.join('video/output', filename)
        cmd = [
            'python', 'balldetect_pos_vel/ball_detect.py',
            '--model_path', 'balldetect_pos_vel/ball_detect.pt',
            '--video_path', input_path,
            '--video_out_path', output_path
        ]

        # [监控点2] 显示子进程输出
        print(f"⚙️ 正在运行检测脚本: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if result.returncode != 0:
            # [监控点3] 处理失败时显示错误
            print(f"❌ 处理失败: {result.stderr}")
            return
        else:
            # [监控点4] 显示成功信息
            print(f"✅ 视频处理完成: {output_path}")

        # 写入处理后的视频记录
        processed_video_id = f"{user_id}_{os.path.splitext(filename)[0]}_{original_video_id.split('_')[-1]}"
        try:
            # [监控点5] 显示数据库操作
            print(f"📝 写入处理视频记录: {processed_video_id}")
            conn = pymysql.connect(**mysql_config)
            with conn.cursor() as cursor:
                sql = """INSERT INTO user_videos_process (video_id, user_id, video_path_process)
                         VALUES (%s, %s, %s)"""
                cursor.execute(sql, (processed_video_id, user_id, output_path))
            conn.commit()
        except Exception as e:
            print(f"❌ 数据库错误: {e}")
        finally:
            conn.close()

        # 提取帧
        frame_output_dir = os.path.join('frames', os.path.splitext(filename)[0])
        os.makedirs(frame_output_dir, exist_ok=True)
        frame_script = [
            'python', 'balldetect_pos_vel/video2frame.py',
            '--video_path', output_path,
            '--output_dir', frame_output_dir,
            '--frame_interval', '1'
        ]

        # [监控点6] 显示帧提取进度
        print(f"🖼️ 开始提取帧到目录: {frame_output_dir}")
        frame_result = subprocess.run(frame_script, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if frame_result.returncode == 0:
            print(f"✅ 帧提取完成，共提取 {len(os.listdir(frame_output_dir))} 帧")
        else:
            print(f"❌ 帧提取失败: {frame_result.stderr}")

        # 写入帧记录
        frame_files = sorted(os.listdir(frame_output_dir))
        # [监控点7] 显示帧记录进度
        print(f"📋 开始写入 {len(frame_files)} 条帧记录...")
        for idx, frame_file in enumerate(frame_files, 1):
            try:
                conn = pymysql.connect(**mysql_config)
                with conn.cursor() as cursor:
                    frame_id = f"{original_video_id}_{idx}"
                    frame_path = os.path.join(frame_output_dir, frame_file)
                    sql = """INSERT INTO video_frames_process (frame_id, video_id, frame_index, frame_path_process)
                             VALUES (%s, %s, %s, %s)"""
                    cursor.execute(sql, (frame_id, original_video_id, idx, frame_path))
                conn.commit()
                # [监控点8] 每10帧打印一次进度
                if idx % 10 == 0:
                    print(f"📥 已写入 {idx}/{len(frame_files)} 帧")
            except Exception as e:
                print(f"❌ 帧记录错误: {e}")
            finally:
                conn.close()
        print(f"✅ 所有帧记录写入完成")

        # 新增：人体骨骼检测处理
        print(f"🧍 开始人体骨骼检测: {filename}")
        os.makedirs('video/output_pose', exist_ok=True)

        pose_cmd = [
            'python', 'mmpose/predict.py',
            'mmpose/utils/coco_person.py',
            'mmpose/utils/model1.pth',
            'mmpose/utils/config.py',
            'mmpose/utils/model2.pth',
            '--input', output_path,
            '--output-root', 'video/output_pose',
            '--device', 'cuda:0',
            '--save-predictions'
        ]

        print(f"⚙️ 正在运行骨骼检测脚本: {' '.join(pose_cmd)}")
        pose_result = subprocess.run(pose_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if pose_result.returncode != 0:
            print(f"❌ 骨骼检测失败: {pose_result.stderr}")
        else:
            print(f"✅ 骨骼检测完成")

            # 提取骨骼帧
            pose_frame_dir = os.path.join('frames', f"{os.path.splitext(filename)[0]}_pose")
            os.makedirs(pose_frame_dir, exist_ok=True)

            pose_video_path = os.path.join('video/output_pose', filename)
            pose_frame_script = [
                'python', 'mmpose/video2frame.py',
                '--video_path', pose_video_path,
                '--output_dir', pose_frame_dir,
                '--frame_interval', '1'
            ]

            print(f"🖼️ 开始提取骨骼帧到目录: {pose_frame_dir}")
            pose_frame_result = subprocess.run(pose_frame_script, capture_output=True, text=True, encoding='utf-8',
                                               errors='ignore')

            if pose_frame_result.returncode == 0:
                print(f"✅ 骨骼帧提取完成，共提取 {len(os.listdir(pose_frame_dir))} 帧")

                # 保存骨骼帧记录到数据库
                pose_frame_files = sorted(os.listdir(pose_frame_dir))
                print(f"📋 开始写入 {len(pose_frame_files)} 条骨骼帧记录...")

                for idx, frame_file in enumerate(pose_frame_files, 1):
                    try:
                        conn = pymysql.connect(**mysql_config)
                        with conn.cursor() as cursor:
                            frame_id = f"{original_video_id}_{idx}"
                            frame_path = os.path.join(pose_frame_dir, frame_file)
                            sql = """INSERT INTO video_frames_pose (frame_id, video_id, frame_index, frame_path)
                                             VALUES (%s, %s, %s, %s)"""
                            cursor.execute(sql, (frame_id, original_video_id, idx, frame_path))
                        conn.commit()
                        if idx % 10 == 0:
                            print(f"📥 已写入 {idx}/{len(pose_frame_files)} 骨骼帧")
                    except Exception as e:
                        print(f"❌ 骨骼帧记录错误: {e}")
                    finally:
                        conn.close()
                print(f"✅ 所有骨骼帧记录写入完成")
            else:
                print(f"❌ 骨骼帧提取失败: {pose_frame_result.stderr}")

    except Exception as e:
        print(f"❌ 异步处理异常: {e}")

        # 更新状态为已完成
    try:
        conn = pymysql.connect(**mysql_config)
        with conn.cursor() as cursor:
            cursor.execute("UPDATE video_status SET status = 3 WHERE video_id = %s",
                           (original_video_id,))
        conn.commit()
        conn.close()
        print(f"✅ 状态更新为已完成")
    except Exception as e:
        print(f"❌ 状态更新错误: {e}")
    finally:
        print(f"🏁 处理任务结束: {filename}\n")