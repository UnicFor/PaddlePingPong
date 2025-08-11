<script setup>
import { ref, computed, onMounted, onBeforeUnmount, defineEmits } from 'vue'
import { useHistoryStore } from '@/stores/history.js'
import ServerGauge from '@/components/ServerGauge.vue'
import CommitHeatmap from '@/components/HeatMap.vue'

const historyStore = useHistoryStore()
const searchQuery = ref('')
const year = ref(new Date().getFullYear())

const emit = defineEmits(['check'])

// 在组件挂载时获取数据
onMounted(() => {
  historyStore.fetchHistory()
  historyStore.startAutoRefresh()
})

// 清理定时器防止内存泄漏
onBeforeUnmount(() => {
  if (historyStore.polling) {
    clearTimeout(historyStore.polling);
    historyStore.polling = null;
  }
})

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString()
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    processing: '分析中',
    completed: '已完成',
    expired: '已失效'
  }
  return statusMap[status] || status
}

// 获取状态样式
const getStatusClass = (status) => {
  return `status-${status}`
}

// 检查是否即将过期
const isExpiringSoon = (expiryDate) => {
  if (!expiryDate) return false
  const expiry = new Date(expiryDate)
  const diffDays = Math.ceil((expiry - Date.now()) / (1000 * 3600 * 24))
  return diffDays <= 3
}

// 检查是否已完成
const isCompleted = (status) => {
  return status.toLowerCase() === 'completed';
}

// 处理删除操作
const handleDelete = async (id) => {
  if (!confirm('确定要永久删除此报告？')) return
  await historyStore.deleteItem(id)
}

// 处理查看操作
const handleCheck = (id) => {
  // 找到对应的分析项
  const item = historyStore.historyItems.find(item => item.id === id);
  
  if (!item) {
    alert('未找到对应的分析项');
    return;
  }
  
  if (!isCompleted(item.status)) {
    console.log('分析尚未完成，无法查看');
    alert('分析尚未完成，无法查看');
    return;
  }

  try {
    // 设置当前分析ID
    historyStore.setCurrentAnalysisId(item.id);
    console.log('已设置当前分析ID:', item.id);

    // 触发check事件，通知父组件(Main.vue)切换到分析页面
    emit('check');

  } catch (error) {
    console.error('查看操作失败:', error);
    alert('查看操作失败，请重试');
  }
}

// 过滤显示的历史记录
const filteredItems = computed(() => {
  return historyStore.historyItems
    .filter(item =>
      item.time.includes(searchQuery.value) ||
      item.status.includes(searchQuery.value)
    )
    .sort((a, b) => b.id - a.id)
})
</script>

<template>
  <section class="analysis-history">
    <h2 class="section-title">分析历史</h2>
    <div class="dashboard-container">
      <div class="heatmap-section">
        <CommitHeatmap :year="year" />
      </div>
      <div class="gauge-section">
        <ServerGauge title="服务器负载监控" />
      </div>
    </div>
    <h2 class="section-title">历史记录</h2>
    <div class="search-filter">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索历史记录（时间）"
      >
    </div>

    <div 
      v-if="historyStore.isLoading && historyStore.historyItems.length === 0" 
      class="loading"
    >
      正在加载历史记录...
    </div>

    <!-- 使用Grid布局的表格 -->
    <div v-else class="table-container">
      <!-- 表头 -->
      <div class="table-header">
        <div>分析时间</div>
        <div>状态</div>
        <div>有效期</div>
        <div>操作</div>
      </div>

      <!-- 表格内容 -->
      <div v-if="filteredItems.length > 0" class="table-content">
        <div v-for="item in filteredItems" :key="item.id" class="history-item">
          <!-- 时间列 -->
          <div class="time-col">
            <span class="analysis-time">{{ formatTime(item.time) }}</span>
          </div>

          <!-- 状态列 -->
          <div class="status-col">
            <span class="status-badge" :class="getStatusClass(item.status)">
              {{ getStatusText(item.status) }}
            </span>
          </div>

          <!-- 有效期列 -->
          <div class="expiry-col">
            <span class="expiry-indicator" :class="{ 'expiring-soon': isExpiringSoon(item.expiry) }">
              {{ formatTime(item.expiry) }}
            </span>
          </div>

          <!-- 操作列 -->
          <div class="action-col">
            <button
              class="check-btn"
              :class="{ disabled: !isCompleted(item.status) }"
              :disabled="!isCompleted(item.status)"
              @click="handleCheck(item.id)"
            >
              查看
            </button>
            <button class="delete-btn" @click="handleDelete(item.id)">
              删除
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="nodata">
        {{ searchQuery ? '无搜索结果' : '暂无数据' }}
      </div>
    </div>

    <div v-if="historyStore.error" class="error-message">
      错误: {{ historyStore.error }}
    </div>

  </section>
</template>

<style scoped>
.section-title {
  white-space: nowrap;
  font-size: 1.5rem;
  margin: 1.5rem 0 1rem;
}

.search-filter input {
  width: 100%;
  max-width: 260px;
  padding: 0.8rem 1.2rem;
  border: 1px solid #e0e6ed;
  border-radius: 25px;
  transition: all 0.3s ease;
}

.search-filter input:focus {
  border-color: #2c3e50;
  box-shadow: 0 2px 8px rgba(44, 62, 80, 0.1);
}

/* 表格容器样式 */
.table-container {
  margin-top: 2rem;        /* 顶部外边距 */
  overflow: hidden;        /* 隐藏溢出内容 */
  min-width: 300px;        /* 最小宽度 */
  box-shadow: 0 2px 8px rgba(44, 62, 80, 0.1);  /* 轻微阴影效果 */
  border-radius: 8px;
}

/* 表头样式 - 使用 Grid 布局 */
.table-header {
  display: grid;           /* 启用 Grid 布局 */
  gap: 1rem;               /* 列间距 */
  grid-template-columns: 2fr 1fr 1.6fr 0.8fr;  /* 定义列宽比例 */
  background: #e1e9ea;
  border-radius: 8px 8px 0 0;
  padding: 1rem 1rem 1rem 2.4rem;
  font-weight: 600;
  color: #5a6a85;
}

/* 表格内容区域样式 */
.table-content {
  background: white;
  border-radius: 0 0 8px 8px;
}

/* 表格行样式 - 与表头使用相同的 Grid 布局 */
.history-item {
  display: grid;           /* 启用 Grid 布局 */
  gap: 1rem;               /* 列间距 */
  grid-template-columns: 2fr 1fr 1.6fr 0.8fr;  /* 与表头相同的列宽比例 */
  padding: 1rem 1rem 1rem 2.4rem;
  border-bottom: 1px solid #f0f0f0;  /* 底部边框 */
  align-items: center;     /* 垂直居中对齐 */
  transition: background-color 0.2s;  /* 背景色过渡效果 */
}

/* 最后一行去除底部边框 */
.history-item:last-child {
  border-bottom: none;
}

/* 鼠标悬停效果 */
.history-item:hover {
  background-color: #f0f0f0;
}

/* 列样式 - 处理内容溢出 */
.time-col, .status-col, .expiry-col, .action-col {
  overflow: hidden;        /* 隐藏溢出内容 */
  text-overflow: ellipsis; /* 溢出文本显示省略号 */
  white-space: nowrap;     /* 不换行 */
}

/* 状态标签样式 */
.status-badge {
  padding: 0.2rem 0.6rem;  /* 内边距 */
  border-radius: 8px;      /* 圆角 */
  font-size: 0.8rem;       /* 小字体 */
  line-height: 1.5;        /* 添加行高属性 */
  display: inline-block;  /* 确保标签正确显示 */
}

/* 不同状态的颜色 */
.status-processing { background-color: #fff3cd; color: #856404; }  /* 分析中 - 黄色 */
.status-completed { background-color: #d4edda; color: #155724; }    /* 已完成 - 绿色 */
.status-expired { background-color: #f8d7da; color: #721c24; }      /* 已失效 - 红色 */

/* 即将过期样式 */
.expiring-soon { color: #dc3545; font-weight: bold; }  /* 红色粗体 */

/* 按钮样式 */
.check-btn, .delete-btn {
  padding: 0.4rem 0.8rem;  /* 内边距 */
  border: none;
  border-radius: 4px;
  cursor: pointer;         /* 鼠标指针 */
  font-size: 0.85rem;      /* 小字体 */
  margin-right: 0.5rem;    /* 右外边距 */
}

.check-btn { background-color: #2c3e50; color: white; }  /* 查看按钮 - 深蓝 */
.check-btn.disabled { background-color: #ccc; cursor: not-allowed; }  /* 禁用状态 */
.delete-btn { background-color: #e74c3c; color: white; }  /* 删除按钮 - 红色 */

@media (max-width: 768px) {
  .table-header, .history-item {
    gap: 0;                /* 取消列间距 */
    padding: 1rem;         /* 减少内边距 */
    grid-template-columns: 3fr 1fr 2fr 1fr;  /* 调整列宽比例 */
  }
}
.loading, .nodata {
  padding: 20px;
  text-align: center;
  color: #666;
  background: white;
  font-weight: 600;
}

.error-message {
  color: #ff4444;
  padding: 10px;
  margin-top: 10px;
  border: 1px solid #ffcccc;
  text-align: center;
}

.dashboard-container {
  display: flex;
  gap: 20px;
}

.heatmap-section {
  flex: 3;
}

.gauge-section {
  flex: 2;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .section-title {
    font-size: 1.2rem;
  }

  .table-header, .history-item {
    gap: 0;
    padding: 1rem;
    grid-template-columns: 3fr 1fr 2fr 1fr;
  }

  .dashboard-container {
    flex-direction: column;
  }
}
</style>