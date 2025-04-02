from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor

# 扩展对象初始化
cors = CORS()
db = SQLAlchemy()
executor = Executor()