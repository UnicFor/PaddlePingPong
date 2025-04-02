import os
import cv2
import argparse


def extract_frames(video_path, output_dir, frame_interval=1):
    """
    从视频中按指定间隔提取帧

    参数：
    video_path: 视频文件路径
    output_dir: 输出目录路径
    frame_interval: 帧间隔（每多少帧保存一帧）
    """
    try:
        # 验证输入路径
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 创建输出目录（包括多层目录）
        os.makedirs(output_dir, exist_ok=True)

        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"无法打开视频文件: {video_path}")

        # 获取视频基本信息
        frame_count = 0
        saved_count = 0
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        print(f"\n开始处理视频: {video_name}")
        print(f"├─ 视频路径: {video_path}")
        print(f"├─ 输出目录: {output_dir}")
        print(f"├─ 总帧数: {total_frames}")
        print(f"└─ 帧间隔: {frame_interval}")

        # 逐帧处理
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                # 生成文件名：视频名_帧号.jpg
                output_path = os.path.join(
                    output_dir,
                    f"{video_name}_{frame_count:06d}.jpg"
                )
                cv2.imwrite(output_path, frame)
                saved_count += 1

            frame_count += 1

        # 释放资源
        cap.release()

        # 输出统计信息
        print(f"\n处理完成:")
        print(f"├─ 实际处理帧数: {frame_count}")
        print(f"├─ 保存帧数: {saved_count}")
        print(f"└─ 保存路径: {os.path.abspath(output_dir)}")

        return True

    except Exception as e:
        print(f"\n错误发生: {str(e)}")
        return False


if __name__ == "__main__":
    # 配置命令行参数
    parser = argparse.ArgumentParser(description='视频帧提取工具')
    parser.add_argument('--video_path', type=str, required=True, help='输入视频路径')
    parser.add_argument('--output_dir', type=str, required=True, help='输出目录路径')
    parser.add_argument('--frame_interval', type=int, default=1, help='帧间隔（默认：1）')

    args = parser.parse_args()

    # 转换为绝对路径
    video_path = os.path.abspath(args.video_path)
    output_dir = os.path.abspath(args.output_dir)

    # 执行帧提取
    success = extract_frames(
        video_path=video_path,
        output_dir=output_dir,
        frame_interval=args.frame_interval
    )

    # 退出码处理
    exit(0 if success else 1)