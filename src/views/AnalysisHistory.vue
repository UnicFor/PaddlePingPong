<script>
import HistoryItem from '@/components/HistoryItem.vue'
import HistoryHeader from '@/components/HistoryHeader.vue'
import { useHistoryStore } from '@/stores/history.js'
import { ref, computed } from 'vue'

export default {
  components: { HistoryItem, HistoryHeader },
  setup() {
    const historyStore = useHistoryStore()
    const searchQuery = ref('')

    // 初始化获取数据
    historyStore.fetchHistory()

    // 统一计算属性
    const filteredItems = computed(() => {
      // 添加空值检查
      if (!historyStore.historyItems) return []
      return historyStore.historyItems
      .filter(item =>
        item.time.includes(searchQuery.value) ||
        item.status.includes(searchQuery.value)
      )
      .sort((a, b) => b.id - a.id);
    })

    const handleDelete = async (id) => {
      await historyStore.deleteItem(id)
    }

    return {
      searchQuery,
      filteredItems,
      handleDelete,
      historyStore
    }
  }
}
</script>

<template>
  <section class="analysis-history">
    <h2 class="section-title">分析历史记录</h2>
    <div class="search-filter">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索历史记录（时间）"
      >
    </div>

    <div v-if="historyStore.isLoading" class="loading">
      正在加载历史记录...
    </div>

    <!-- 表格结构 -->
    <div v-else>
      <div class="table-body">
        <!-- 独立表头组件 -->
        <HistoryHeader />
        <!-- 使用div模拟表格行 -->
        <HistoryItem
          v-for="item in filteredItems"
          :key="item.id"
          :item="item"
          @delete="handleDelete"
          @check="$emit('check')"
        />

        <!-- 空状态 -->
        <div v-if="!filteredItems.length" class="nodata">
          {{ searchQuery ? '无搜索结果' : '暂无数据' }}
        </div>
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

.table-body{
  margin-top: 2rem;
  overflow: hidden;
  min-width: 300px;
  box-shadow: 0 2px 8px rgba(44, 62, 80, 0.1);
  border-radius: 8px;
}

.loading,
.nodata {
  padding: 20px;
  text-align: center;
  color: #666;
  background: white;
  font-weight: 600;
}

.loading {
  margin-top: 2rem;
}

.error-message {
  color: #ff4444;
  padding: 10px;
  margin-top: 10px;
  border: 1px solid #ffcccc;
  text-align: center;
}

@media (max-width: 768px) {
  .section-title{
    font-size: 1.2rem;
  }
}
</style>