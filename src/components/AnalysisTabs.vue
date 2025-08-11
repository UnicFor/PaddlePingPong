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
          v-if="!loading && !error"
          :content="reportContent"
          class="markdown-viewer"
        />

        <!-- 下载按钮 -->
        <div class="download-section">
          <button
            @click="downloadReport"
            class="download-button"
            :disabled="!reportContent"
          >
            下载pdf报告
          </button>
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
import html2pdf from 'html2pdf.js'
import AnalysisCharts from '@/components/AnalysisCharts.vue'
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

const downloadReport = () => {
  const tempDiv = document.createElement('div')

  // 1. 设置容器样式（关键修复）
  Object.assign(tempDiv.style, {
  width: '180mm', // A4宽度(210mm) - 左右边距各15mm = 180mm
  minHeight: '280mm', // 留出顶部底部边距空间
  margin: '0 auto', // 水平居中
  padding: '10mm', // 统一使用mm单位
  background: 'white',
  boxSizing: 'border-box', // 关键：确保padding不增加总宽度
  visibility: 'visible',
  position: 'static'
  })

  // 2. 添加完整样式
  tempDiv.innerHTML = `
  <div class="markdown-content" style="max-width: 100%; overflow-wrap: break-word;">
    ${marked.parse(reportContent.value)}
  </div>
  <style>
    /* 基础字体 */
    body {
      font: 12pt/1.5 'SimHei', SimSun, sans-serif;
      color: #333;
    }

    /* 标题层次 */
    h1 { font-size: 18pt; margin: 12pt 0; }
    h2 { font-size: 16pt; margin: 10pt 0; }
    h3 { font-size: 14pt; margin: 8pt 0; }

    /* 表格处理 */
    table {
      width: 100% !important;
      table-layout: fixed; /* 防止表格溢出 */
      margin: 8pt 0;
    }
    td, th {
      word-break: break-word; /* 强制换行 */
      padding: 4pt;
    }

    /* 代码块 */
    pre {
      max-width: 100%;
      white-space: pre-wrap; /* 允许换行 */
      background: #f8f8f8;
      padding: 8pt;
      border-radius: 4pt;
    }
  </style>
  `

  document.body.appendChild(tempDiv)

  // 3. 优化PDF配置
  const options = {
    margin: [10, 6, 10, 10], // 上右下左边距
    filename: `${props.videoId}_analysis_report.pdf`,
    image: {
      type: 'jpeg',
      quality: 0.98 // 提高图片质量
    },
    html2canvas: {
      scale: 4, // 关键：提高分辨率
      useCORS: true,
      letterRendering: true, // 启用字体抗锯齿
      logging: true // 调试时开启
    },
    jsPDF: {
      unit: 'mm',
      format: 'a4',
      orientation: 'portrait',
      hotfixes: ['px_scaling'] // 修复像素缩放问题
    }
  }

  // 4. 添加渲染延迟
  setTimeout(() => {
    html2pdf()
      .set(options)
      .from(tempDiv)
      .save()
      .finally(() => {
        document.body.removeChild(tempDiv)
      })
  }, 800) // 确保DOM渲染完成
}
</script>

<style scoped src="@/assets/css/analysis-tab.css"></style>