<script>
import { useHistoryStore } from '@/stores/history.js'

export default {
  props: {
    item: {
      type: Object,
      required: true
    }
  },
  computed: {
    formattedTime() {
      return new Date(this.item.time).toLocaleString()
    },
    statusText() {
      const statusMap = {
        processing: '分析中',
        completed: '已完成',
        expired: '已失效'
      }
      return statusMap[this.item.status]
    },
    statusClass() {
      return `status-${this.item.status}`
    },
    isExpiringSoon() {
      const expiryDate = new Date(this.item.expiry)
      const diffDays = Math.ceil((expiryDate - Date.now()) / (1000 * 3600 * 24))
      return diffDays <= 3
    },
    isCompleted() {
      return this.item.status === 'completed'
    }
  },
  methods: {
    handleDelete() {
      if (!confirm('确定要永久删除此报告？')) return
      this.$emit('delete', this.item.id)
    },
    handleCheck() {
      const historyStore = useHistoryStore()
      historyStore.setCurrentAnalysisId(this.item.id)
      this.$emit('check')
    }
  },
  emits: ['check', 'delete']
}
</script>

<template>
  <div class="history-item">
    <!-- 时间列 -->
    <div class="time-col">
      <span class="analysis-time">{{ formattedTime }}</span>
    </div>

    <!-- 状态列 -->
    <div class="status-col">
      <span class="status-badge" :class="statusClass">
        {{ statusText }}
      </span>
    </div>

    <!-- 有效期列 -->
    <div class="expiry-col">
      <span class="expiry-indicator" :class="{ 'expiring-soon': isExpiringSoon }">
        {{ item.expiry }}
      </span>
    </div>

    <!-- 操作列 -->
    <div>
      <button
        class="check-btn"
        :class="{ disabled: !isCompleted }"
        :disabled="!isCompleted"
        @click="handleCheck"
      >
        查看
      </button>
      <button class="delete-btn" @click="handleDelete">
        删除
      </button>
    </div>
  </div>
</template>

<style scoped src="@/assets/css/history-item.css"></style>