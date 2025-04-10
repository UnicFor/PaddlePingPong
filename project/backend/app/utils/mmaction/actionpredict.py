# ---------- 第一部分：视频分割处理（修改版，增加元数据记录） ----------
import os
import csv
import cv2
import decord
import numpy as np
from pathlib import Path
from tqdm import tqdm
import shutil
import argparse


class LongVideoSplitter:
    def __init__(self,
                 input_path,
                 output_dir,
                 target_frames=8,
                 stride=4,
                 min_fill_frames=3,
                 resize_size=(256, 256)):
        # 初始化路径参数
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 视频处理参数
        self.target_frames = target_frames
        self.stride = stride
        self.min_fill = min_fill_frames
        self.resize_size = resize_size

        # 初始化视频读取器
        self.vr = decord.VideoReader(str(self.input_path))
        self.total_frames = len(self.vr)
        self.fps = self.vr.get_avg_fps()

        # 元数据存储
        self.metadata = []

        # 视频编码器设置
        self.fourcc = self._get_supported_codec()

    def _get_supported_codec(self):
        codec_priority = ['mp4v', 'avc1', 'XVID', 'MJPG']
        test_path = self.output_dir / "test_temp.mp4"

        for codec in codec_priority:
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            writer = cv2.VideoWriter(
                str(test_path),
                fourcc,
                self.fps,
                self.resize_size
            )
            if writer.isOpened():
                writer.release()
                os.remove(test_path)
                print(f"使用编码器: {codec}")
                return fourcc
        raise RuntimeError("未找到可用视频编码器")

    def _padding_frames(self, frames):
        current_frames = len(frames)
        if current_frames < self.min_fill:
            return self._circular_padding(frames)
        else:
            return self._hybrid_padding(frames)

    def _circular_padding(self, frames):
        """循环填充直到达到目标帧数"""
        # 将numpy数组转换为帧列表
        frames_list = [frame for frame in frames]
        padded = []
        while len(padded) < self.target_frames:
            padded.extend(frames_list)
        return np.array(padded[:self.target_frames])

    def _hybrid_padding(self, frames):
        """首尾混合填充"""
        # 将numpy数组转换为帧列表
        frames_list = [frame for frame in frames]
        pad_len = self.target_frames - len(frames_list)

        # 创建填充帧时确保使用拷贝
        head = [np.copy(frames_list[0]) for _ in range(pad_len // 2)]
        tail = [np.copy(frames_list[-1]) for _ in range(pad_len - pad_len // 2)]

        return np.array(head + frames_list + tail)  # 转换为numpy数组

    def _save_segment(self, frames, segment_name):
        output_path = self.output_dir / segment_name
        writer = cv2.VideoWriter(
            str(output_path),
            self.fourcc,
            self.fps,
            self.resize_size
        )
        for frame in frames:
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            resized = cv2.resize(bgr_frame, self.resize_size)
            writer.write(resized)
        writer.release()

    def process(self):
        start_idx = 0
        segment_count = 0
        pbar = tqdm(total=self.total_frames, desc="处理进度")

        while start_idx < self.total_frames:
            end_idx = start_idx + self.target_frames
            segment_name = f"{self.input_path.stem}_{segment_count:03d}.mp4"

            if end_idx <= self.total_frames:
                indices = list(range(start_idx, end_idx))
                frames = self.vr.get_batch(indices).asnumpy()
                self._save_segment(frames, segment_name)
                meta_end = end_idx - 1
                progress = self.stride
            else:
                remaining = self.total_frames - start_idx
                if remaining * 2 >= self.stride:
                    indices = list(range(start_idx, self.total_frames))
                    frames = self.vr.get_batch(indices).asnumpy()
                    padded_frames = self._padding_frames(frames)
                    self._save_segment(padded_frames, segment_name)
                    meta_end = self.total_frames - 1
                    progress = self.total_frames - start_idx
                else:
                    progress = self.total_frames - start_idx
                    pbar.update(progress)
                    break

            # 记录元数据
            self.metadata.append({
                'video_name': segment_name,
                'start_frame': start_idx,
                'end_frame': meta_end
            })

            segment_count += 1
            start_idx += self.stride
            pbar.update(progress)

        pbar.close()
        # 保存元数据
        metadata_path = self.output_dir / "metadata.csv"
        with open(metadata_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['video_name', 'start_frame', 'end_frame'])
            for m in self.metadata:
                writer.writerow([m['video_name'], m['start_frame'], m['end_frame']])
        print(f"处理完成，共生成 {segment_count} 个视频片段")


# ---------- 第二部分：预测处理（修改版，整合元数据） ----------
def run_inference(config_path,
                  checkpoint_path,
                  label_map,
                  video_dir,
                  output_csv):
    import pandas as pd
    from mmaction.apis import init_recognizer, inference_recognizer

    device = 'cuda:0'
    num_topk = 5

    # 初始化模型
    model = init_recognizer(config_path, checkpoint_path, device=device)

    # 读取元数据
    metadata = pd.read_csv(Path(video_dir) / 'metadata.csv')
    meta_dict = metadata.set_index('video_name').to_dict('index')

    # 读取标签
    with open(label_map, 'r', encoding='utf-8') as f:
        labels = [line.strip() for line in f]

    # 准备CSV文件
    headers = ['video_name', 'start_frame', 'end_frame', 'predicted_class', 'confidence'] + \
              [f'top{i + 1}_class' for i in range(num_topk)] + [f'top{i + 1}_score' for i in range(num_topk)]

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        # 获取视频文件列表
        video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]

        for video_name in sorted(video_files):
            video_path = os.path.join(video_dir, video_name)
            meta = meta_dict.get(video_name, {})

            try:
                results = inference_recognizer(model, video_path)
                topk_indices = results.pred_score.argsort(descending=True)[:num_topk]
                topk_scores = results.pred_score[topk_indices].cpu().numpy().round(4)
                topk_classes = [labels[i] for i in topk_indices]

                row = [
                    video_name,
                    meta.get('start_frame', -1),
                    meta.get('end_frame', -1),
                    topk_classes[0],
                    f"{topk_scores[0]:.4f}",
                    *topk_classes,
                    *[f"{s:.4f}" for s in topk_scores]
                ]
                writer.writerow(row)
                print(f'Success: {video_name}')
            except Exception as e:
                print(f'Error processing {video_name}: {str(e)}')
                row = [video_name, -1, -1, 'ERROR', '0.0000'] + [''] * (2 * num_topk)
                writer.writerow(row)


def visualize_results(video_path,
                      result_csv,
                      output_video_path,
                      top_i=3):
    import cv2
    import pandas as pd
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    # 加载预测结果（带topN信息）
    df = pd.read_csv(result_csv, encoding='utf-8')
    valid_df = df[df['predicted_class'] != 'ERROR']
    valid_df['start_frame'] = valid_df['start_frame'].astype(int)
    valid_df['end_frame'] = valid_df['end_frame'].astype(int)

    # 初始化视频读取
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 加载中文字体（请确保此路径存在或替换为系统中的实际字体路径）
    fontpath = "C:/Windows/Fonts/simhei.ttf"  # 微软黑体
    font_size = 24

    # 初始化视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

        # 查找匹配的时间窗口
        matches = valid_df[
            (valid_df['start_frame'] <= current_frame) &
            (valid_df['end_frame'] >= current_frame)
            ]

        if not matches.empty:
            # 转换为PIL图像以支持中文文字
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            font = ImageFont.truetype(fontpath, font_size)

            # 绘制前i个预测结果
            y = 120
            for _, row in matches.iterrows():
                # 遍历前i个预测类别
                for j in range(top_i):
                    class_name = row[f"top{j + 1}_class"]
                    confidence = row[f"top{j + 1}_score"]
                    text = f"Top{j + 1}: {class_name} ({confidence:.2f})"
                    draw.text((20, y), text, font=font, fill=(0, 255, 0))
                    y += 35  # 调整行间距

            # 将PIL图像转回OpenCV格式
            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        out.write(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"结果视频已保存至: {output_video_path}")

# ---------- 执行入口 ----------
if __name__ == "__main__":

    # 配置命令行参数
    parser = argparse.ArgumentParser(description='视频帧提取工具')
    parser.add_argument('--config_path', type=str, required=True,help='模型配置文件路径')
    parser.add_argument('--checkpoint_path', type=str, required=True,help='模型权重文件路径')
    parser.add_argument('--label_map', type=str, required=True,help='标签映射文件路径')
    parser.add_argument('--video_path', type=str, required=True, help='输入视频路径')
    parser.add_argument('--output_dir', type=str, required=True, help='输出目录路径')
    parser.add_argument('--filename', type=str, required=True, help='文件名')
    args = parser.parse_args()

    # 转换为绝对路径
    config_path = os.path.abspath(args.config_path)
    checkpoint_path = os.path.abspath(args.checkpoint_path)
    label_map = os.path.abspath(args.label_map)
    input_video = os.path.abspath(args.video_path)
    output_dir = os.path.abspath(args.output_dir)
    output_video=os.path.join(output_dir, args.filename)
    split_dir = os.path.join(output_dir, "split_videos")

    filename = os.path.basename(args.filename)
    base_name = os.path.splitext(filename)[0]
    csv_filename = f"{base_name}.csv"
    prediction_csv = os.path.join(output_dir, csv_filename)

    try:
        # 步骤1：视频分割
        splitter = LongVideoSplitter(
            input_path=input_video,
            output_dir=split_dir,
            target_frames=8,
            stride=8,
            resize_size=(256, 256)
            )
        splitter.process()

        # 步骤2：执行预测
        run_inference(config_path,
                  checkpoint_path,
                  label_map,
                  split_dir,
                  prediction_csv)
        visualize_results(input_video,prediction_csv,output_video,3)
    finally:
        # 清理分割视频文件夹（无论是否出错都会执行）
        if Path(split_dir).exists():
            shutil.rmtree(split_dir)
            print(f"\n已清理临时分割文件夹: {split_dir}")
