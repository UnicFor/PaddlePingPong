<template>
  <div class="analysis-tabs">
    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab"
        :class="{ active: activeTab === tab }"
        @click="activeTab = tab"
      >
        {{ tab }}
      </button>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === '分析报告'">
        <!-- PDF 查看器 -->
        <!-- 加载状态 -->
        <div v-if="loading" class="loading">报告加载中...</div>

        <!-- 错误提示 -->
        <div v-if="error" class="error">{{ error }}</div>

        <!-- Markdown 查看器 -->
        <MarkdownRenderer
          v-show="!loading && !error"
          :content="reportContent"
          :cache-key="props.videoId"
          class="markdown-viewer"
        />

        <!-- 下载按钮 -->
        <div class="download-section">
          <button
            @click="mddownloadReport"
            class="download-button"
            :disabled="!reportContent"
          >
            下载md报告
          </button>
        </div>
      </div>

      <div v-if="activeTab === '可视化图表'">
        <AnalysisCharts
          :video-id="videoId"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import {onMounted, ref, watch} from 'vue'
import AnalysisCharts from '@/components/Charts/AnalysisCharts.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { useAuthStore } from '@/stores/auth'
import {marked} from "marked";

const auth = useAuthStore()

const activeTab = ref('分析报告')
const tabs = ref(['分析报告','可视化图表'])
const reportContent = ref('')
const loading = ref(false)
const error = ref(null)

const props = defineProps({
  videoId: {
    type: String,
    required: true
  }
})

onMounted(() => {
  if (activeTab.value === '分析报告') {
    fetchReport()
  }
})

watch(activeTab, (newTab) => {
  if (newTab === '分析报告' && !reportContent.value) {
    fetchReport()
  }
})

const fetchReport = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await fetch(`/api/report/${props.videoId}`, {
      headers: {
        Authorization: `Bearer ${auth.token}`
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || '获取报告失败')
    }

    reportContent.value = await response.text()
  } catch (err) {
    error.value = err.message || '报告加载失败，请稍后重试'
    console.error('加载报告失败:', err)
  } finally {
    loading.value = false
  }
}

const mddownloadReport = () => {
  const blob = new Blob([reportContent.value], { type: 'text/markdown' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${props.videoId}_analysis_report.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.analysis-tabs {
  background: white;
  border-radius: 10px;
  min-height: 60vh;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.tab-nav {
  display: flex;
  border-bottom: 2px solid #f1f3f5;
  padding: 0 20px;
}

.tab-nav button {
  flex: 1;
  flex-shrink: 0;
  white-space: nowrap;
  min-width: 110px;
  padding: 16px 20px;
  border: none;
  background: none;
  color: #95a5a6;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition:
    color 0.3s ease,
    background 0.3s ease;
  position: relative;
}

.tab-nav button.active {
  color: #2c3e50;
}

.tab-nav button.active::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 3px;
  background: #2c3e50;
  border-radius: 2px;
}

.tab-content {
  padding: 25px;
}

.report-section {
  animation: fadeIn 0.4s ease forwards;
}

.chart-placeholder {
  height: 400px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px dashed #eceff1;
  margin-bottom: 25px;
}

.action-buttons {
  display: flex;
  gap: 15px;
  margin-top: 25px;
}

.action-buttons button {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 8px;
  background: #2c3e50;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    background 0.3s ease;
}

.action-buttons button:hover {
  background: #34495e;
  transform: translateY(-2px);
}

.action-buttons button:active {
  transform: translateY(0);
}

.event-list {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #f1f3f5;
}

.event-item {
  padding: 16px;
  background: white;
  border-bottom: 1px solid #f8f9fa;
  transition: background 0.2s ease;
}

.event-item:hover {
  background: #f8f9fa;
}

.event-time {
  color: #7f8c8d;
  font-size: 13px;
  font-family: monospace;
}

.event-desc {
  color: #2c3e50;
  font-size: 14px;
}

.loading {
  padding: 20px;
  color: #666;
  text-align: center;
}

.error {
  color: #ff4444;
  padding: 15px;
  background: #ffeeee;
  border-radius: 4px;
  margin: 10px;
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
  margin-top: 20px;
}

.download-button {
  background-color: #2c3e50;
  margin: 0 10px 0 10px;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.download-button:hover {
  background-color: #273646;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .analysis-tabs {
    border-radius: 6px;
  }
  .tab-nav {
    padding: 0;
  }
}
</style>