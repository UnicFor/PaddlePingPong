<script setup>
import {onMounted, computed, ref, watch} from 'vue'
import AnalysisCharts from '@/components/Charts/AnalysisCharts.vue'
import ReportArea from '@/components/ReportArea.vue'
import request from '@/utils/request'

const activeTab = ref('report')
const tabs = ref([
  { key: 'report', label: '分析报告', component: ReportArea },
  { key: 'charts', label: '可视化图表', component: AnalysisCharts }
])
const reportContent = ref('')
const loading = ref(false)
const error = ref(null)

const props = defineProps({
  videoId: {
    type: String,
    required: true
  }
})

// 需要缓存的组件名称
const cachedComponents = ref(['AnalysisCharts'])

// 当前动态组件
const currentComponent = computed(() => {
  const currentTab = tabs.value.find(tab => tab.key === activeTab.value)
  return currentTab?.component || 'ReportArea'
})

// 获取报告数据
const fetchReport = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await request.get(`/api/report/${props.videoId}`)
    reportContent.value = response.data

  } catch (err) {
    error.value = err.message || '报告加载失败，请稍后重试'
    console.error('加载报告失败:', err)
  } finally {
    loading.value = false
  }
}

// 下载报告
const mddownloadReport = () => {
  const blob = new Blob([reportContent.value], { type: 'text/markdown' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${props.videoId}_analysis_report.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 监听标签切换
watch(activeTab, (newTab) => {
  if (newTab === 'report' && !reportContent.value) {
    fetchReport()
  }
})

// 组件挂载时加载报告
onMounted(() => {
  if (activeTab.value === 'report') {
    fetchReport()
  }
})
</script>

<template>
  <div class="analysis-tabs">
    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <keep-alive :include="cachedComponents">
        <component 
          :is="currentComponent" 
          :video-id="videoId"
          :content="reportContent"
          :loading="loading"
          :error="error"
          :cache-key="videoId"
          @download="mddownloadReport"
          @retry="fetchReport"
        />
      </keep-alive>
    </div>
  </div>
</template>

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
  transition: all 0.3s ease;
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

/* 动态组件动画 */
.tab-content > * {
  animation: fadeIn 0.3s ease forwards;
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