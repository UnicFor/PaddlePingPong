import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),  // 保留Vue开发工具插件
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))  // 保留路径别名
    }
  },
  // 新增与Flask整合的配置
  build: {
    outDir: '../backend/app/static',  // 构建到Flask的静态目录
    assetsDir: 'assets',              // 静态资源子目录
    emptyOutDir: true,                // 构建时清空目标目录
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/js/[name]-[hash].js',  // 优化chunk文件组织
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    }
  },
  server: {
    port: 3000,                      // 前端开发端口
    proxy: {
      '/api': {                      // 代理所有/api请求到Flask
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '')  // 移除/api前缀
      }
    }
  }
})