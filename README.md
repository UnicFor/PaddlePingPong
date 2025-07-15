# 智能乒乓球运动分析与可视化前端

本项目是基于 Vue 3 + Vite 的智能乒乓球运动分析与可视化系统前端，结合飞桨（PaddlePaddle）、文心大模型等AI能力，致力于为用户提供高效、智能、可视化的运动分析体验。

## 项目亮点

- **AI驱动的智能分析**：集成飞桨深度学习框架与文心大模型，实现非接触式动作捕捉、人体关键点识别、球拍姿态解算、轨迹预测等前沿功能。
- **多维度运动评估**：支持动作质量评分、技战术分析、训练建议生成、损伤风险预测等，助力科学训练。
- **高质量数据可视化**：采用 Three.js、ECharts 等前端可视化技术，支持运动轨迹热力图、3D动作重建、生物力学分析、对抗模拟推演等多种数据展示方式。
- **现代化交互体验**：界面简洁美观，支持视频上传、帧级分析、AI问答等丰富功能，移动端自适应，用户体验优秀。
- **灵活的架构设计**：前后端分离，接口灵活，易于扩展和二次开发。

## 技术栈

- Vue 3 + Vite
- Pinia 状态管理
- Vue Router 路由
- Axios 网络请求
- Three.js、ECharts 数据可视化
- 飞桨（PaddlePaddle）、文心大模型（后端AI能力）

## 快速开始

```sh
npm install
npm run dev
```

访问：http://localhost:3000

## 构建生产环境

```sh
npm run build
```

## 推荐开发环境

- [VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar)（建议禁用Vetur）

## 目录结构简介

- `src/components`：核心UI组件（如视频分析、侧边栏、用户面板等）
- `src/views`：主要页面（欢迎页、分析页、历史、技术问答等）
- `src/stores`：Pinia 状态管理
- `src/assets`：静态资源与样式
- `src/router`：前端路由配置

<details>
<summary>前端主要目录结构说明</summary>

```
src/
├── assets/                # 静态资源与样式
│   ├── css/               # 各功能模块独立CSS
│   ├── default-avatar.png
│   └── ...                # 其他图片资源
├── components/            # 可复用UI组件
│   ├── FramePanel.vue
│   ├── SidebarNav.vue
│   ├── VideoComparator.vue
│   └── ...                # 其他组件
├── views/                 # 页面视图
│   ├── Main.vue
│   ├── Analysis.vue
│   ├── LoginView.vue
│   └── ...                # 其他页面
├── stores/                # Pinia状态管理
│   ├── auth.js
│   └── history.js
├── router/                # 路由配置
│   └── index.js
├── App.vue                # 根组件
└── main.js                # 入口文件
```
</details>

## 后续优化建议

1. 增强前端性能（如骨架屏、懒加载、虚拟滚动等）。
2. 丰富3D可视化与动画效果，提升交互沉浸感。
3. 增加国际化（i18n）支持，适配多语言用户。
4. 优化移动端体验，适配更多终端。
5. 加强前后端接口容错与异常处理，提升健壮性。
6. 引入自动化测试（单元、端到端）保障质量。
7. 支持PWA，提升离线可用性和安装体验。

---

如需更多帮助或有建议，欢迎提 issue 或联系开发者。
