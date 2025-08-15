<script setup>
import { ref, computed, onMounted, onBeforeUnmount, defineEmits, watch } from 'vue'
import { useHistoryStore } from '@/stores/history.js'

const historyStore = useHistoryStore()

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
  const date = new Date(time)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}年${month}月${day}日 ${hours}:${minutes}`
}

// 格式化有效期
const formatExpiry = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}年${month}月${day}日`
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

// 获取缓存状态文本
const getCacheText = (status) => {
  const cacheMap = {
    cached: '已缓存',
    not_cached: '未缓存',
    checking: '检查中'
  }
  return cacheMap[status] || '未知'
}

// 获取缓存状态样式
const getCacheClass = (status) => {
  return `cache-${status}`
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

// 处理查看操作
const handleCheck = (id) => {
  // 找到对应的分析项
  const item = historyStore.historyItems.find(item => item.id === id);
  
  if (!item) {
    alert('未找到对应的分析项');
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

// 处理缓存操作
const handleCacheOperation = async (item) => {
  try {
    if (item.cacheStatus === 'cached') {
      // 清除缓存需要二次确认
      if (!confirm('确定要清除此报告的缓存数据吗？此操作不可恢复。')) {
        return;
      }
      await historyStore.clearCacheForItem(item.id)
      alert('缓存已清除')
    } else {
      // 添加缓存
      if (!confirm('确定要缓存此报告的数据吗？这将占用本地存储空间。')) {
        return;
      }
      await historyStore.cacheItem(item.id)
      alert('数据已缓存')
    }
  } catch (error) {
    console.error('缓存操作失败:', error)
    alert('缓存操作失败，请重试')
  }
}

const currentPage = ref(1)
const itemsPerPage = 8

// 处理删除操作
const handleDelete = async (id) => {
  if (!confirm('确定要永久删除此报告？')) return
  await historyStore.deleteItem(id)
}

// 筛选状态
const filters = ref({
  date: '',
  status: '',
  isCached: ''
})

// 重置筛选
const resetFilters = () => {
  filters.value = {
    date: '',
    status: '',
    isCached: ''
  }
}

// 过滤显示的历史记录
const filteredItems = computed(() => {
  let items = historyStore.historyItems
  
  // 日期筛选
  if (filters.value.date) {
    const filterDate = new Date(filters.value.date)
    items = items.filter(item => {
      const itemDate = new Date(item.time)
      return itemDate.toDateString() === filterDate.toDateString()
    })
  }
  
  // 状态筛选
  if (filters.value.status) {
    items = items.filter(item => item.status === filters.value.status)
  }
  
  // 是否缓存筛选
  if (filters.value.isCached !== '') {
    const isCachedFilter = filters.value.isCached === 'true'
    items = items.filter(item => 
      (item.cacheStatus === 'cached') === isCachedFilter
    )
  }
  
  return items.sort((a, b) => b.id - a.id)
})

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(filteredItems.value.length / itemsPerPage)
})

// 计算当前页显示的数据
const paginatedItems = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  return filteredItems.value.slice(startIndex, endIndex)
})

// 跳转到指定页
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// 上一页
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

// 下一页
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// 计算页码显示范围
const pageNumbers = computed(() => {
  const pages = []
  const startPage = Math.max(1, currentPage.value - 2)
  const endPage = Math.min(totalPages.value, currentPage.value + 2)
  
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }
  return pages
})
</script>

<template>
  <section class="analysis-history">
    <h2 class="section-title">历史记录</h2>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <label>日期</label>
        <input 
          type="date" 
          v-model="filters.date"
          class="filter-input"
        />
      </div>
      
      <div class="filter-group">
        <label>状态</label>
        <select v-model="filters.status" class="filter-select">
          <option value="">全部状态</option>
          <option value="processing">分析中</option>
          <option value="completed">已完成</option>
          <option value="expired">已失效</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>是否缓存</label>
        <select v-model="filters.isCached" class="filter-select">
          <option value="">全部</option>
          <option value="true">已缓存</option>
          <option value="false">未缓存</option>
        </select>
      </div>
      
      <button class="reset-btn" @click="resetFilters">重置</button>
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
        <div>缓存状态</div>
        <div>操作</div>
      </div>

      <!-- 表格内容 -->
      <div v-if="paginatedItems.length > 0" class="table-content">
        <div v-for="item in paginatedItems" :key="item.id" class="history-item">
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
            <span class="expiry-time" :class="{ 'expiring-soon': isExpiringSoon(item.expiry) }">
              {{ formatExpiry(item.expiry) }}
            </span>
          </div>

          <!-- 缓存情况列 -->
          <div class="cache-col">
            <span class="cache-badge" :class="getCacheClass(item.cacheStatus)">
              {{ getCacheText(item.cacheStatus) }}
            </span>
          </div>

          <!-- 操作列 -->
          <div class="action-col">
            <button
              class="check-btn"
              :class="{ disabled: !isCompleted(item.status) && item.cacheStatus !== 'cached' }"
              :disabled="!isCompleted(item.status) && item.cacheStatus !== 'cached'"
              @click="handleCheck(item.id)"
            >
              查看结果
            </button>
            <button 
              class="cache-btn"
              :class="{ disabled: !isCompleted(item.status), 'cached': item.cacheStatus === 'cached' }"
              :disabled="!isCompleted(item.status)"
              @click="handleCacheOperation(item)"
            >
              {{ item.cacheStatus === 'cached' ? '清除缓存' : '缓存数据' }}
            </button>
            <button 
              class="delete-btn" 
              @click="handleDelete(item.id)"
            >
              删除记录
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="nodata">
        {{ searchQuery ? '无搜索结果' : '暂无数据' }}
      </div>

      <!-- 分页控件 -->
      <div v-if="totalPages > 1" class="pagination">
        <button 
          class="page-btn" 
          @click="prevPage" 
          :disabled="currentPage === 1"
        >
          上一页
        </button>
        
        <button 
          v-for="page in pageNumbers" 
          :key="page"
          class="page-btn"
          :class="{ active: page === currentPage }"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
        
        <button 
          class="page-btn" 
          @click="nextPage" 
          :disabled="currentPage === totalPages"
        >
          下一页
        </button>
        
        <span class="page-info">
          第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
        </span>
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

/* 筛选栏样式 */
.filter-bar {
  display: flex;
  gap: 1.5rem;
  align-items: end;
  margin: 1.5rem 0;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(44, 62, 80, 0.08);
  flex-wrap: wrap;
  border: 1px solid #e8ecf0;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 140px;
}

.filter-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #5a6a85;
  margin-bottom: 0.2rem;
}

.filter-input, .filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid #d1d9e0;
  border-radius: 8px;
  font-size: 0.9rem;
  background: white;
  transition: all 0.2s ease;
  color: #2c3e50;
}

.filter-input:hover, .filter-select:hover {
  border-color: #b8c1cc;
}

.reset-btn {
  padding: 0.75rem 1.5rem;
  background: #2c3e50;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 400;
  transition: all 0.2s ease;
  align-self: end;
  margin-bottom: 0.1rem;
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
.table-header, .history-item {
    display: grid;           /* 启用 Grid 布局 */
    gap: 1rem;               /* 列间距 */
    grid-template-columns: 2fr 1fr 1fr 1fr 2fr;;  /* 定义列宽比例 */
    align-items: center;
    padding: 1rem 1rem 1rem 2.4rem;
}

.table-header {
    background: #e1e9ea;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    color: #5a6a85;
}

/* 表格内容区域样式 */
.table-content {
    background: white;
    border-radius: 0 0 8px 8px;
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
.time-col, .status-col, .expiry-col, .cache-col, .action-col {
  overflow: hidden;        /* 隐藏溢出内容 */
  text-overflow: ellipsis; /* 溢出文本显示省略号 */
  white-space: nowrap;     /* 不换行 */
}

.analysis-time, .expiry-time {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

/* 即将过期样式 */
.expiring-soon { color: #dc3545; font-weight: bold; }  /* 红色粗体 */

/* 标签样式 */
.status-badge, .cache-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.5;
  display: inline-block;  /* 确保标签正确显示 */
}

.status-processing { background-color: #fff3cd; color: #856404; }
.status-completed { background-color: #d4edda; color: #155724; }
.status-expired { background-color: #f8d7da; color: #721c24; }

.cache-badge {
    background-color: #ffedf7; color: #8c1932;
}

.cache-cached { background-color: #d4edda; color: #155724; }
.cache-checking { background-color: #fff3cd; color: #856404; }

/* 按钮样式 */
.check-btn, .delete-btn, .cache-btn {
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;         /* 鼠标指针 */
  font-size: 0.85rem;
  margin-right: 0.5rem;
}

.check-btn { background-color: #2c3e50; color: white; }
.delete-btn { background-color: #e74c3c; color: white; }
.cache-btn { background-color: #00792e; color: white; }

.check-btn.disabled { background-color: #ccc; cursor: not-allowed; }
.cache-btn.disabled { background-color: #ccc; cursor: not-allowed; }

.cache-btn.cached { background-color: #6c757d; color: white; }

/* 分页控件样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: white;
  border-top: 1px solid #e0e6ed;
  border-radius: 0 0 8px 8px;
}

.page-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  color: #333;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.page-btn:hover:not(:disabled) {
  background: #f0f0f0;
  border-color: #2c3e50;
}

.page-btn.active {
  background: #2c3e50;
  color: white;
  border-color: #2c3e50;
}

.page-btn:disabled {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
  border-color: #ddd;
}

.page-info {
  margin-left: 1rem;
  color: #666;
  font-size: 0.9rem;
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

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-select {
    width: 100%;
  }

  .table-header, .history-item {
    gap: 0;
    padding: 0.8rem;
    grid-template-columns: 2fr 1fr 1.5fr 1fr 1.5fr;
    font-size: 0.9rem;
  }

  .dashboard-container {
    flex-direction: column;
  }

  .pagination {
    flex-wrap: wrap;
    gap: 0.3rem;
  }
  
  .page-btn {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
  }
  
  .page-info {
    margin-left: 0.5rem;
    font-size: 0.8rem;
  }
}
</style>
