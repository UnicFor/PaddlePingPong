<script setup>
import FramePanel from '@/components/FramePanel.vue'
import AnalysisTabs from '@/components/AnalysisTabs.vue'
import VideoComparator from "@/components/VideoComparator.vue";
import axios from 'axios'

import { computed, ref, watch } from 'vue'
import { useHistoryStore } from '@/stores/history.js'
import { useAuthStore } from '@/stores/auth'

const historyStore = useHistoryStore()
const auth = useAuthStore()
const originalUrl = ref('')
const processedUrl = ref('')
const loading = ref(false)
const error = ref(null)
const currentVideoId = ref(null)

const currentAnalysis = computed(() =>
  historyStore.historyItems.find(
    item => item.id === historyStore.currentAnalysisId
  )
)

const formattedTime = computed(() =>
  currentAnalysis.value
    ? new Date(currentAnalysis.value.time).toLocaleString()
    : ''
)

const fetchVideoUrls = async (videoId) => {
  try {
    loading.value = true
    const token = auth.token
    const response = await axios.get(`/api/video/${videoId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    if (response.data.success) {
      originalUrl.value = response.data.data.original
      processedUrl.value = response.data.data.processed || ''
    }
  } catch (err) {
    error.value = err.response?.data?.message || '获取视频地址失败'
  } finally {
    loading.value = false
  }
}

watch(() => currentAnalysis.value?.video_id, (newVideoId) => {
  if (newVideoId) {
    fetchVideoUrls(newVideoId)
  }
}, { immediate: true })

watch(() => historyStore.currentAnalysisId, (newId) => {
  const analysis = historyStore.historyItems.find(item => item.id === newId)
  currentVideoId.value = analysis?.video_id || null
}, { immediate: true })

watch(currentVideoId, (newId) => {
  if (newId) {
    fetchVideoUrls(newId)
  }
})
</script>

<!-- Analysis.vue -->
<template>
  <div class="analysis-container">
    <h2 class="section-title">分析汇总界面 - {{ formattedTime }}</h2>
    <div class="content-wrapper">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading">加载中...</div>

      <!-- 错误提示 -->
      <div v-if="error" class="error">{{ error }}</div>
      <VideoComparator
        :original-src="originalUrl"
        :processed-src="processedUrl"
      />
      <FramePanel
          v-if="currentAnalysis?.video_id && !loading"
          :video-id="currentAnalysis.video_id"
      />
      <AnalysisTabs />
    </div>
  </div>
</template>

<style scoped>
.analysis-container {
  flex-direction: row;
  min-width: 320px;
}

.section-title {
  white-space: nowrap;
}

.content-wrapper {
  display: block;
}

.loading {
  color: #666;
  padding: 20px;
}

.error {
  color: #ff4444;
  padding: 10px;
}

@media (max-width: 768px) {
  .analysis-container{
    font-size: 0.8rem;
  }
}
</style>