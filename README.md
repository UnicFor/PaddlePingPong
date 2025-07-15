# PaddlePingPong（后端文件）
### 前端文件参考Frontend分支

## 核心框架

[![Flask](https://img.shields.io/badge/Flask-2.0.x-blue)](https://flask.palletsprojects.com/)
[![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen)](https://vuejs.org/)

## 相关技术栈

**后端服务**  
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0.x-blue?logo=flask)
![Flask-CORS](https://img.shields.io/badge/Flask--CORS-3.0.x-lightgrey)

**前端服务**  
![Vue3](https://img.shields.io/badge/Vue-3.x-brightgreen?logo=vue.js)
![Pinia](https://img.shields.io/badge/Pinia-2.x-orange?logo=vue.js)
![Vue Router](https://img.shields.io/badge/vue_router-4.x-green?logo=vue.js)
![Vite](https://img.shields.io/badge/Vite-4.x-purple?logo=vite)
![Axios](https://img.shields.io/badge/Axios-1.x-blueviolet)
![ESLint](https://img.shields.io/badge/ESLint-8.x-red?logo=eslint)

---

# 项目详细说明

## 项目简介

PaddlePingPong 是一个基于 Flask+Vue 的乒乓球运动分析平台后端。支持用户管理、视频上传与处理、骨骼点与动作识别、RAG 智能分析、历史记录等功能。前后端分离，前端基于 Vue3，后端为 RESTful API 服务。

---

## 目录结构

```
project/backend/app/
├── __init__.py           # Flask应用工厂
├── config.py             # 配置管理（数据库、静态目录等）
├── extensions.py         # 扩展初始化（CORS、SQLAlchemy等）
├── errors.py             # 错误处理（建议完善）
├── routes/               # 路由模块（按功能拆分）
│   ├── user.py           # 用户相关接口
│   ├── auth.py           # 认证与登录
│   ├── video.py          # 视频处理
│   ├── frames.py         # 视频帧处理
│   ├── rag.py            # RAG智能分析
│   └── ...               # 其他功能
├── static/               # 前端静态资源（Vue打包产物）
├── utils/                # 工具与业务逻辑
│   ├── models.py         # ORM数据模型
│   ├── security.py       # JWT安全工具
│   ├── mmpose/           # 姿态识别相关
│   ├── mmaction/         # 动作识别相关
│   ├── balldetect_pos_vel/ # 乒乓球检测
│   └── ...               # 其他工具
└── run.py                # 启动入口
```

---

## 主要功能

- 用户注册、登录、信息管理（JWT认证）
- 视频上传、分帧、骨骼点与动作识别
- RAG（Retrieval-Augmented Generation）智能分析与报告生成
- 历史记录与结果管理
- 前后端分离，支持 CORS

---

## 环境依赖

- Python 3.9+
- Flask 3.1.0
- Flask-CORS 5.0.1
- Flask-Executor 1.0.0
- Flask-SQLAlchemy 3.1.1
- PyJWT、python-dotenv、PyMySQL
- OpenCV、faiss-cpu、mmpose、mmaction2、langchain、openai 等
- 详细依赖见 [`project/requirementx.txt`](project/requirementx.txt)

安装依赖：
```bash
pip install -r project/requirementx.txt
```

---

## 数据库说明

- 默认使用 MySQL，连接配置见 `config.py`，如：
  ```
  SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/fwwb?charset=utf8mb4'
  ```
- 主要表结构见 `utils/models.py`，包括用户、视频、历史记录、帧、处理状态等。
- 初始化数据库（需先创建数据库 `fwwb`）：
  ```python
  # 进入Python交互环境
  from app import create_app
  from utils.models import db
  app = create_app()
  with app.app_context():
      db.create_all()
  ```

---

## 配置说明

- 配置文件：`config.py`，支持开发/生产环境切换。
- 推荐使用 `.env` 管理敏感信息（如 SECRET_KEY、数据库密码、OpenAI Key 等）。
```python
# routes/.env
QIANFAN_API_KEY=""
OPENAI_API_KEY=""
OPENAI_API_BASE=""
```
- 静态资源目录为 `static/`，前端需先打包产物至此目录。

---

## 启动方式

```bash
cd project/backend/
pip install -r ../requirementx.txt
python run.py
```
- 默认监听 `0.0.0.0:5000`，可通过 `config.py` 修改端口和调试模式。

---

## 安全与认证

- 采用 JWT 认证，所有受保护接口需在请求头携带 `Authorization: Bearer <token>`。
- 登录/注册接口获取 token，后续请求需带 token。
- 认证装饰器详见 `utils/security.py`。

---

## 前后端联动

- 前端 Vue3 项目打包后，将 `dist` 目录内容复制到 `static/` 目录下。
- 后端通过 `/static/` 路径托管前端资源，API 路径统一为 `/api/` 前缀。

---

## 常见问题

1. **依赖安装失败？**
   - 检查 Python 版本（推荐 3.9+），建议使用虚拟环境。
   - 部分 AI/ML 依赖（如 mmpose、mmaction2、faiss-cpu）需科学上网或提前下载好 wheel 包。

2. **数据库连接失败？**
   - 确认 MySQL 服务已启动，`config.py` 中账号密码正确，且已创建 `fwwb` 数据库。

3. **前端无法访问 API？**
   - 检查 CORS 配置，开发环境下允许 `http://localhost:3000`。

4. **模型文件缺失或推理报错？**
   - 检查 `utils/mmpose/utils/`、`utils/mmaction/utils/`、`utils/balldetect_pos_vel/` 等目录下模型文件是否齐全。

---
