from utils.model import BallTrackerNet
import torch
import cv2
from utils.general_back import postprocess
from tqdm import tqdm
import numpy as np
import argparse
from itertools import groupby
from scipy.spatial import distance


def read_video(path_video):
    """ Read video file
    :params
        path_video: path to video file
    :return
        frames: list of video frames
        fps: frames per second
    """
    cap = cv2.VideoCapture(path_video)
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
        else:
            break
    cap.release()
    return frames, fps


def infer_model(frames, model, fps):  # 添加fps参数
    """ Run pretrained model on a consecutive list of frames
    :params
        frames: list of consecutive video frames
        model: pretrained model
        fps: frames per second of the video
    :return
        ball_track: list of detected ball points
        dists: list of euclidean distances between two neighbouring ball points
        output_video: list of processed frames
    """
    # cv2.namedWindow("Processing Preview", cv2.WINDOW_NORMAL)

    height = 360
    width = 640
    dists = [-1] * 2
    ball_track = [(None, None)] * 2
    output_video = []
    for num in tqdm(range(2, len(frames))):
        original_frame = frames[num]
        orig_height, orig_width = original_frame.shape[:2]

        img = cv2.resize(frames[num], (width, height))
        img_prev = cv2.resize(frames[num - 1], (width, height))
        img_preprev = cv2.resize(frames[num - 2], (width, height))
        imgs = np.concatenate((img, img_prev, img_preprev), axis=2)
        imgs = imgs.astype(np.float32) / 255.0
        imgs = np.rollaxis(imgs, 2, 0)
        inp = np.expand_dims(imgs, axis=0)
        out = model(torch.from_numpy(inp).float().to(device))
        output = out.argmax(dim=1).detach().cpu().numpy()

        scale_x = orig_width / width
        scale_y = orig_height / height

        x_pred, y_pred = postprocess(output, scale_x, scale_y)
        ball_track.append((x_pred, y_pred))

        if ball_track[-1][0] and ball_track[-2][0]:
            dist = distance.euclidean(ball_track[-1], ball_track[-2])
        else:
            dist = -1
        dists.append(dist)

        # 生成预览帧
        preview_frame = frames[num].copy()

        # 获取当前坐标
        current_x, current_y = x_pred, y_pred

        # 生成坐标文本
        coord_line = f"X: {current_x:.1f}" if current_x else "X: NaN"
        coord_line += f"  Y: {current_y:.1f}" if current_y else "  Y: NaN"

        # 计算速度
        current_dist = dists[num]
        if current_dist != -1 and current_x is not None and current_y is not None and ball_track[num - 1][
            0] is not None:
            speed = current_dist * fps
            speed_line = f"Speed: {speed:.1f} px/s"
        else:
            speed_line = "Speed: N/A"

        # 设置显示参数
        text_scale = 1.2
        text_thickness = 2
        text_color = (255, 255, 255)
        bg_color = (40, 40, 40)

        # 计算文本尺寸
        (coord_width, coord_height), _ = cv2.getTextSize(coord_line, cv2.FONT_HERSHEY_SIMPLEX, text_scale,
                                                         text_thickness)
        (speed_width, speed_height), _ = cv2.getTextSize(speed_line, cv2.FONT_HERSHEY_SIMPLEX, text_scale,
                                                         text_thickness)
        max_width = max(coord_width, speed_width)
        total_height = coord_height + speed_height + 5

        # 绘制背景
        cv2.rectangle(preview_frame,
                      (10, 10),
                      (20 + max_width, 20 + total_height),
                      bg_color, -1)

        # 绘制坐标行
        cv2.putText(preview_frame, coord_line,
                    (20, 20 + coord_height),
                    cv2.FONT_HERSHEY_SIMPLEX, text_scale,
                    text_color, text_thickness)

        # 绘制速度行
        cv2.putText(preview_frame, speed_line,
                    (20, 20 + coord_height + 5 + speed_height),
                    cv2.FONT_HERSHEY_SIMPLEX, text_scale,
                    text_color, text_thickness)

        # 绘制轨迹
        for i in range(10):
            idx = num - i
            if idx >= 0 and ball_track[idx][0]:
                color = (0, 0, 255) if i == 0 else (0, 255, 0)
                cv2.circle(preview_frame,
                           (int(ball_track[idx][0]), int(ball_track[idx][1])),
                           radius=3, color=color, thickness=-1)

        # 显示预览
        # cv2.imshow("Processing Preview", cv2.resize(preview_frame, (orig_width, orig_height)))
        output_video.append(preview_frame)

        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()
    return ball_track, dists, output_video


def remove_outliers(ball_track, dists, max_dist=100):
    """ Remove outliers from model prediction
    :params
        ball_track: list of detected ball points
        dists: list of euclidean distances between two neighbouring ball points
        max_dist: maximum distance between two neighbouring ball points
    :return
        ball_track: list of ball points
    """
    outliers = list(np.where(np.array(dists) > max_dist)[0])
    # Create a copy to safely iterate while modifying
    outliers_copy = outliers.copy()

    for i in outliers_copy:
        # Check if i+1 is within bounds
        if i + 1 < len(dists):
            if (dists[i + 1] > max_dist) | (dists[i + 1] == -1):
                ball_track[i] = (None, None)
                if i in outliers:  # Check if still in list before removing
                    outliers.remove(i)
        # Handle case where i is at the end of the list
        elif i == len(dists) - 1:
            ball_track[i] = (None, None)

        # Check bounds before accessing i-1
        if i > 0 and dists[i - 1] == -1:
            ball_track[i - 1] = (None, None)

    return ball_track


def split_track(ball_track, max_gap=4, max_dist_gap=80, min_track=5):
    """ Split ball track into several subtracks in each of which we will perform
    ball interpolation.
    :params
        ball_track: list of detected ball points
        max_gap: maximun number of coherent None values for interpolation
        max_dist_gap: maximum distance at which neighboring points remain in one subtrack
        min_track: minimum number of frames in each subtrack
    :return
        result: list of subtrack indexes
    """
    list_det = [0 if x[0] else 1 for x in ball_track]
    groups = [(k, sum(1 for _ in g)) for k, g in groupby(list_det)]

    cursor = 0
    min_value = 0
    result = []
    for i, (k, l) in enumerate(groups):
        if (k == 1) & (i > 0) & (i < len(groups) - 1):
            dist = distance.euclidean(ball_track[cursor - 1], ball_track[cursor + l])
            if (l >= max_gap) | (dist / l > max_dist_gap):
                if cursor - min_value > min_track:
                    result.append([min_value, cursor])
                    min_value = cursor + l - 1
        cursor += l
    if len(list_det) - min_value > min_track:
        result.append([min_value, len(list_det)])
    return result


def interpolation(coords):
    """ Run ball interpolation in one subtrack
    :params
        coords: list of ball coordinates of one subtrack
    :return
        track: list of interpolated ball coordinates of one subtrack
    """

    def nan_helper(y):
        return np.isnan(y), lambda z: z.nonzero()[0]

    x = np.array([x[0] if x[0] is not None else np.nan for x in coords])
    y = np.array([x[1] if x[1] is not None else np.nan for x in coords])

    nons, yy = nan_helper(x)
    x[nons] = np.interp(yy(nons), yy(~nons), x[~nons])
    nans, xx = nan_helper(y)
    y[nans] = np.interp(xx(nans), xx(~nans), y[~nans])

    track = [*zip(x, y)]
    return track


def write_track(frames, ball_track, path_output_video, fps, trace=7):
    """ Write .avi file with detected ball tracks
    :params
        frames: list of original video frames
        ball_track: list of ball coordinates
        path_output_video: path to output video
        fps: frames per second
        trace: number of frames with detected trace
    """
    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # 或者尝试 *'h264'/*'X264'
    out = cv2.VideoWriter(path_output_video, fourcc, fps, (width, height))

    for frame in frames:
        out.write(frame)
    out.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch_size', type=int, default=2, help='batch size')
    parser.add_argument('--model_path', type=str, help='path to model')
    parser.add_argument('--video_path', type=str, help='path to input video')
    parser.add_argument('--video_out_path', type=str, help='path to output video')
    parser.add_argument('--extrapolation', action='store_true', help='whether to use ball track extrapolation')
    args = parser.parse_args()

    model = BallTrackerNet()
    device = 'cuda'
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model = model.to(device)
    model.eval()

    frames, fps = read_video(args.video_path)
    ball_track, dists, processed_frames = infer_model(frames, model, fps)  # 传递fps参数
    ball_track = remove_outliers(ball_track, dists)

    if args.extrapolation:
        subtracks = split_track(ball_track)
        for r in subtracks:
            ball_subtrack = ball_track[r[0]:r[1]]
            ball_subtrack = interpolation(ball_subtrack)
            ball_track[r[0]:r[1]] = ball_subtrack

    write_track(processed_frames, ball_track, args.video_out_path, fps)