# 🏓 智能乒乓球运动分析与可视化前端

> 基于 Vue 3 + Vite 的现代化乒乓球运动分析平台前端

## 📋 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [开发规范](#开发规范)
- [部署说明](#部署说明)
- [后续计划](#后续计划)

## 🎯 项目简介

本项目是一个基于现代Web技术栈的乒乓球运动分析与可视化平台前端，专注于提供专业的运动数据分析和直观的可视化展示。项目采用前后端分离架构，与基于Flask的后端服务无缝对接。

### 核心能力
- ✅ 视频上传与帧级分析
- ✅ 人体关键点检测与可视化
- ✅ 运动轨迹分析与图表展示
- ✅ AI驱动的技术分析报告
- ✅ 实时数据缓存与优化
- ✅ 响应式设计，支持多端访问

## 🛠️ 技术栈

### 核心技术
| 类别 | 技术栈 | 版本 |
|------|--------|------|
| **前端框架** | Vue.js | 3.5.13 |
| **构建工具** | Vite | 6.1.0 |
| **状态管理** | Pinia | 3.0.1 |
| **路由管理** | Vue Router | 4.5.0 |
| **UI框架** | Element Plus | 2.10.6 |

### 可视化与数据处理
| 类别 | 技术栈 | 用途 |
|------|--------|------|
| **图表库** | ECharts 6.0 | 数据可视化 |
| **数据处理** | PapaParse | CSV数据解析 |
| **缓存** | IndexedDB | 本地数据缓存 |

### 开发工具
| 类别 | 工具 | 用途 |
|------|------|------|
| **开发工具** | Vue DevTools | 调试工具 |
| **代码规范** | ESLint | 代码检查 |
| **类型支持** | JSConfig | 路径别名配置 |

## ✨ 功能特性

### 1. 视频分析系统
- **多格式支持**：支持MP4、AVI等主流视频格式
- **帧提取**：精确到帧的视频分析
- **姿态检测**：基于PaddlePaddle的人体关键点检测
- **轨迹追踪**：乒乓球运动轨迹可视化

### 2. 数据可视化
- **实时图表**：加速度、速度、角度等多维度数据展示
- **交互式图表**：支持缩放、筛选、对比
- **3D重建**：三维姿态重建与动画演示
- **热力图**：运动区域热力分布分析

### 3. AI分析引擎
- **智能报告**：基于大模型的技术分析报告
- **模式识别**：运动模式识别与分类
- **建议生成**：个性化训练建议
- **RAG系统**：检索增强生成技术

### 4. 用户体验
- **响应式设计**：完美适配桌面、平板、手机
- **离线缓存**：关键数据本地缓存
- **实时反馈**：操作状态即时反馈
- **无障碍访问**：键盘导航、屏幕阅读器支持

## 🚀 快速开始

### 环境要求
- Node.js >= 18.0.0
- npm >= 9.0.0

### 安装依赖
```bash
npm install
```

### 开发环境启动
```bash
npm run dev
```
访问地址：http://localhost:3000

### 生产环境构建
```bash
npm run build
```

### 预览构建结果
```bash
npm run preview
```

## 📁 项目结构
```
├── 📋 项目配置
│   ├── .env                    # 环境变量
│   ├── .env.development        # 开发环境配置
│   ├── .env.production         # 生产环境配置
│   ├── vite.config.js          # Vite构建配置
│   ├── jsconfig.json           # JavaScript配置
│   └── package.json            # 依赖管理

├── 🎯 源代码目录
│   ├── src/
│   │   ├── 📱 主应用
│   │   │   ├── main.js         # 应用入口
│   │   │   ├── App.vue         # 根组件
│   │   │   └── router/index.js # 路由配置
│   │   │
│   │   ├── 🗄️ 状态管理
│   │   │   ├── stores/
│   │   │   │   ├── auth.js     # 认证状态
│   │   │   │   └── history.js  # 历史记录
│   │   │   └── composables/    # 组合式函数
│   │   │       ├── frameCache.js    # 帧缓存管理
│   │   │       └── usePoseDataLoader.js # 姿态数据加载
│   │   │
│   │   ├── 🎨 组件体系
│   │   │   ├── components/
│   │   │   │   ├── Base/       # 基础组件
│   │   │   │   │   ├── Abstract.vue      # 摘要组件
│   │   │   │   │   ├── SideNav.vue       # 侧边导航
│   │   │   │   │   ├── UserPanel.vue     # 用户面板
│   │   │   │   │   └── ServerMonitor.vue # 服务器监控
│   │   │   │   │
│   │   │   │   ├── Analysis/   # 分析组件
│   │   │   │   │   ├── AnalysisCharts.vue # 分析图表
│   │   │   │   │   ├── AnalysisHistory.vue # 历史记录
│   │   │   │   │   ├── AnalysisTabs.vue    # 标签页
│   │   │   │   │   └── ReportArea.vue      # 报告区域
│   │   │   │   │
│   │   │   │   ├── Charts/     # 图表组件
│   │   │   │   │   ├── AccelerationChart.vue # 加速度图
│   │   │   │   │   ├── SpeedChart.vue        # 速度图
│   │   │   │   │   └── TimelineChart.vue     # 时间轴图
│   │   │   │   │
│   │   │   │   └── Video/      # 视频组件
│   │   │   │       ├── VideoPanel.vue      # 视频面板
│   │   │   │       ├── FramePanel.vue      # 帧面板
│   │   │   │       ├── VideoComparator.vue # 视频对比
│   │   │   │       └── VideoControls.vue   # 视频控制
│   │   │
│   │   ├── 📄 页面视图
│   │   │   ├── views/
│   │   │   │   ├── WelcomeView.vue    # 欢迎页
│   │   │   │   ├── LoginView.vue      # 登录页
│   │   │   │   ├── Main.vue          # 主页面
│   │   │   │   ├── Analysis.vue      # 分析页
│   │   │   │   ├── AnalysisMain.vue  # 分析主页
│   │   │   │   ├── TechnicalEvaluation.vue # 技术评估
│   │   │   │   ├── Test.vue          # 测试页
│   │   │   │   └── Login/            # 登录相关
│   │   │   │       ├── RegisterView.vue      # 注册
│   │   │   │       └── ChangePasswordView.vue # 改密码
│   │   │
│   │   ├── 🛠️ 工具函数
│   │   │   └── utils/
│   │   │       ├── request.js      # HTTP请求封装
│   │   │       ├── dataFitting.js   # 数据拟合
│   │   │       └── debounce.js      # 防抖函数
│   │   │
│   │   └── 🎨 静态资源
│   │       └── assets/
│   │           ├── css/            # 样式文件
│   │           ├── picture/        # 图片资源
│   │           └── test-data/      # 测试数据
│   │
│   └── 📱 移动端适配
│       └── 响应式CSS设计
├── 🚀 开发工具
│   ├── .vscode/extensions.json    # VSCode推荐插件
│   └── .gitignore               # Git忽略文件
```

## 🔧 开发规范

### 代码规范
- 使用ESLint进行代码检查
- 遵循Vue 3 Composition API规范
- 组件命名采用PascalCase
- 文件命名采用kebab-case

### 提交规范
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 代码重构
test: 测试相关
chore: 构建/工具


### 分支管理
- `main`: 生产分支
- `dev`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复

## 🚀 部署说明

### 开发环境
```bash
# 克隆项目
git clone [repository-url]

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 生产部署
```bash
# 构建生产版本
npm run build

# 构建文件将输出到 Flask 后端静态目录
```

### Docker部署（可选）
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 📋 后续计划

### 近期计划（2025 Q3）
- [ ] TypeScript迁移
- [ ] 单元测试集成
- [ ] 组件文档生成
- [ ] 性能优化（懒加载、缓存）

### 长期计划（2025 Q4+）
- [ ] 微前端架构
- [ ] WebAssembly集成
- [ ] 边缘计算支持
- [ ] AI模型优化

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

**⭐ 如果这个项目对你有帮助，请给个Star！**
