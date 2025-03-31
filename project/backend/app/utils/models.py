from ..extensions import db
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """用户模型（对应你现有的users表）"""
    __tablename__ = 'users'  # 显式指定表名

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    weixin = db.Column(db.String(50))
    registration_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    role = db.Column(db.String(20), default='member')

    def to_dict(self):
        """将用户对象转换为字典"""
        return {
            "phone": self.phone,
            "weixin": self.weixin or "",
            "username": self.username,
            "registration_date": self.registration_date.strftime("%Y-%m-%d"),
            "user_role": self.role
        }

    def set_password(self, password):
        """生成安全密码哈希"""
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:1000000'
        )

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'