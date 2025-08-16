
<script setup>
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  },
  cacheKey: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['download', 'retry'])
</script>

<template>
  <div class="report-area">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>报告加载中...</p>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="$emit('retry')" class="retry-button">重试</button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!content" class="empty-state">
      <div class="empty-icon">📄</div>
      <p>暂无报告内容</p>
    </div>

    <!-- Markdown 查看器 -->
    <template v-else>
      <MarkdownRenderer
        :content="content"
        :cache-key="cacheKey"
        class="markdown-viewer"
      />

      <!-- 下载按钮 -->
      <div class="download-section">
        <button
          @click="$emit('download')"
          class="download-button"
          :disabled="!content"
        >
          下载md报告
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.report-area {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2c3e50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

.error-icon, .empty-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.error p, .empty-state p {
  color: #666;
  margin-bottom: 15px;
}

.retry-button {
  background: #ff4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background: #ff2222;
}

.markdown-viewer {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.download-section {
  text-align: center;
  margin-top: 30px;
}

.download-button {
  background-color: #2c3e50;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.download-button:hover:not(:disabled) {
  background-color: #273646;
  transform: translateY(-2px);
}

.download-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  transform: none;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .markdown-viewer {
    padding: 15px;
    margin: 0 10px;
  }
}
</style>