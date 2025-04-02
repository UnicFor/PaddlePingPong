from ..extensions import db
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Date
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    user_id = db.Column(Integer, primary_key=True, autoincrement=True)
    username = db.Column(String(20), unique=True, nullable=False)
    phone = db.Column(String(11), unique=True, nullable=False)
    password_hash = db.Column(String(128), nullable=False)
    weixin = db.Column(String(150), default='')
    registration_date = db.Column(db.DateTime, default=datetime.now,
                                 server_default=db.func.current_timestamp())
    role = db.Column(String(20), default='member')

    # 关系定义
    histories = db.relationship('History', backref='user', lazy='dynamic')
    videos = db.relationship('UserVideo', backref='user', lazy='dynamic')
    processed_videos = db.relationship('UserVideoProcess', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:1000000'
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "phone": self.phone,
            "weixin": self.weixin,
            "registration_date": self.registration_date.strftime("%Y-%m-%d %H:%M:%S"),
            "role": self.role
        }

class History(db.Model):
    """历史记录"""
    __tablename__ = 'history'

    history_id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer, ForeignKey('users.user_id'), nullable=False)
    video_id = db.Column(String(512), ForeignKey('user_videos.video_id'), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now,
                           server_default=db.func.current_timestamp())
    status = db.Column(String(20), nullable=False)
    expiry = db.Column(Date)

    def to_dict(self):
        return {
            "id": self.history_id,
            "user_id": self.user_id,
            "time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "expiry": self.expiry.strftime("%Y-%m-%d") if self.expiry else None
        }

class UserVideo(db.Model):
    """用户上传视频"""
    __tablename__ = 'user_videos'

    video_id = db.Column(String(512), primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.user_id'), nullable=False)
    video_path = db.Column(String(255), nullable=False)

    # 关系定义
    pose_frames = db.relationship('VideoFramesPose', backref='video', lazy='dynamic')
    processed_frames = db.relationship('VideoFramesProcess', backref='video', lazy='dynamic')
    status = db.relationship('VideoStatus', backref='video', uselist=False)

    def to_dict(self):
        return {
            "video_id": self.video_id,
            "user_id": self.user_id,
            "video_path": self.video_path,
            "status": self.status.status if self.status else None
        }

class UserVideoProcess(db.Model):
    """处理后的视频"""
    __tablename__ = 'user_videos_process'

    video_id = db.Column(String(512), primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.user_id'), nullable=False)
    video_path_process = db.Column(String(255), nullable=False)

    def to_dict(self):
        return {
            "video_id": self.video_id,
            "user_id": self.user_id,
            "video_path_process": self.video_path_process
        }

class VideoFramesPose(db.Model):
    """姿态分析帧"""
    __tablename__ = 'video_frames_pose'

    frame_id = db.Column(String(512), primary_key=True)
    video_id = db.Column(String(512), ForeignKey('user_videos.video_id'), nullable=False)
    frame_index = db.Column(Integer, nullable=False)
    frame_path = db.Column(String(512), nullable=False)

    def to_dict(self):
        return {
            "frame_id": self.frame_id,
            "video_id": self.video_id,
            "frame_index": self.frame_index,
            "frame_path": self.frame_path
        }

class VideoFramesProcess(db.Model):
    """处理后的视频帧"""
    __tablename__ = 'video_frames_process'

    frame_id = db.Column(String(512), primary_key=True)
    video_id = db.Column(String(512), ForeignKey('user_videos.video_id'), nullable=False)
    frame_index = db.Column(Integer, nullable=False)
    frame_path_process = db.Column(String(512), nullable=False)

    def to_dict(self):
        return {
            "frame_id": self.frame_id,
            "video_id": self.video_id,
            "frame_index": self.frame_index,
            "frame_path_process": self.frame_path_process
        }

class VideoStatus(db.Model):
    """视频处理状态"""
    __tablename__ = 'video_status'

    video_id = db.Column(String(512), ForeignKey('user_videos.video_id'), primary_key=True)
    status = db.Column(Integer, nullable=False)

    def to_dict(self):
        return {
            "video_id": self.video_id,
            "status": self.status
        }