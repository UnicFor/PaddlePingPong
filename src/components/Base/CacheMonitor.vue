<script setup>
import { ref, onMounted } from 'vue'
import frameCache from '@/composables/frameCache'

const stats = ref({
  totalVideos: 0,
  totalSize: 0,
  totalFrames: 0,
  maxCacheSize: 0,
  usagePercent: 0
})

const maxCacheSizeMB = ref(500) // 默认500MB
const loading = ref(false)
const clearing = ref(false)
const error = ref(null)

// 新增：弹窗相关状态
const showSettingsModal = ref(false)
const tempCacheSize = ref(500)
const updatingCacheSize = ref(false)

// 格式化字节大小
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取进度条样式类
const getProgressClass = () => {
  const percent = stats.value.usagePercent || 0
  if (percent > 90) return 'danger'
  if (percent > 75) return 'warning'
  return 'normal'
}

const refreshStats = async () => {
  try {
    loading.value = true
    error.value = null
    
    const globalStats = await frameCache.getGlobalCacheStats()
    stats.value = globalStats
    
    // 更新输入框的值
    maxCacheSizeMB.value = Math.round(globalStats.maxCacheSize / 1024 / 1024)
    tempCacheSize.value = maxCacheSizeMB.value
  } catch (err) {
    error.value = '获取缓存统计失败: ' + err.message
    console.error('获取缓存统计失败:', err)
  } finally {
    loading.value = false
  }
}

// 打开设置弹窗
const openSettingsModal = () => {
  tempCacheSize.value = maxCacheSizeMB.value
  showSettingsModal.value = true
}

// 关闭设置弹窗
const closeSettingsModal = () => {
  showSettingsModal.value = false
  tempCacheSize.value = maxCacheSizeMB.value
}

// 保存缓存上限设置
const saveCacheSettings = async () => {
  try {
    updatingCacheSize.value = true
    error.value = null
    
    // 验证输入
    if (!tempCacheSize.value || tempCacheSize.value < 100 || tempCacheSize.value > 5000) {
      throw new Error('缓存上限必须在100-5000MB之间')
    }
    
    // 设置新的缓存上限
    frameCache.setMaxCacheSize(tempCacheSize.value)
    maxCacheSizeMB.value = tempCacheSize.value
    
    // 立即刷新统计
    await refreshStats()
    
    // 关闭弹窗
    closeSettingsModal()
    
    // 显示成功提示
    console.log(`缓存上限已设置为 ${maxCacheSizeMB.value}MB`)
  } catch (err) {
    error.value = '更新缓存上限失败: ' + err.message
    console.error('更新缓存上限失败:', err)
  } finally {
    updatingCacheSize.value = false
  }
}

// 清空所有缓存
const clearAllCache = async () => {
  if (!confirm('确定要清空所有本地缓存吗？此操作不可恢复！')) {
    return
  }
  
  try {
    clearing.value = true
    error.value = null
    
    await frameCache.clear()
    await refreshStats()
    
    console.log('缓存已清空！')
  } catch (err) {
    error.value = '清空缓存失败: ' + err.message
    console.error('清空缓存失败:', err)
  } finally {
    clearing.value = false
  }
}

// 初始化
onMounted(async () => {
  await refreshStats()
})
</script>

<template>
  <div class="cache-monitor">
    <h3>本地缓存监控</h3>
    
    <div class="cache-stats">
      <div class="stat-item">
        <span class="label">缓存视频数:</span>
        <span class="value">{{ stats.totalVideos }}</span>
        <span class="label">缓存占用空间:</span>
        <span class="value">{{ formatBytes(stats.totalSize) }}</span>
      </div>
      
      <div class="stat-item">
        <span class="label">使用率:</span>
        <span class="value">{{ stats.usagePercent?.toFixed(1) || 0 }}%</span>
      </div>
    </div>

    <div class="progress-container">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: `${Math.min(stats.usagePercent || 0, 100)}%` }"
          :class="getProgressClass()"
        ></div>
      </div>
      <span class="progress-text">
        {{ formatBytes(stats.totalSize || 0) }} / {{ formatBytes(stats.maxCacheSize || 0) }}
      </span>
    </div>

    <div class="cache-actions">
      <button @click="refreshStats" :disabled="loading" class="refresh-btn">
        {{ loading ? '刷新中...' : '刷新统计' }}
      </button>
      
      <button @click="openSettingsModal" class="settings-btn">
        设置缓存上限
      </button>
      
      <button @click="clearAllCache" :disabled="clearing" class="clear-btn">
        {{ clearing ? '清理中...' : '清空所有缓存' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- 设置弹窗 -->
    <div v-if="showSettingsModal" class="modal-overlay" @click="closeSettingsModal">
      <div class="modal-content" @click.stop>
        <h4>设置缓存上限</h4>
        
        <div class="modal-body">
          <label>缓存上限 (MB):</label>
          <input 
            type="number" 
            v-model.number="tempCacheSize"
            min="100"
            max="5000"
            class="modal-input"
            placeholder="输入缓存上限"
          />
          <p class="help-text">建议范围：100-5000MB</p>
        </div>
        
        <div class="modal-actions">
          <button @click="closeSettingsModal" class="cancel-btn">取消</button>
          <button 
            @click="saveCacheSettings" 
            :disabled="updatingCacheSize"
            class="confirm-btn"
          >
            {{ updatingCacheSize ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cache-monitor {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.cache-stats {
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.label {
  font-weight: 500;
  color: #666;
}

.value {
  font-weight: bold;
  color: #333;
}

.progress-container {
  margin-bottom: 20px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 5px;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-fill.normal {
  background: #52c41a;
}

.progress-fill.warning {
  background: #faad14;
}

.progress-fill.danger {
  background: #ff4d4f;
}

.progress-text {
  font-size: 12px;
  color: #666;
}

.cache-actions {
  display: flex;
  gap: 10px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.refresh-btn {
  background: #1890ff;
  color: white;
}

.refresh-btn:hover:not(:disabled) {
  background: #40a9ff;
}

.settings-btn {
  background: #52c41a;
  color: white;
}

.settings-btn:hover:not(:disabled) {
  background: #73d13d;
}

.clear-btn {
  background: #ff4d4f;
  color: white;
}

.clear-btn:hover:not(:disabled) {
  background: #ff7875;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  margin-top: 10px;
  padding: 10px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  color: #ff4d4f;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 400px;
}

.modal-content h4 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.modal-body {
  margin-bottom: 20px;
}

.modal-body label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #666;
}

.modal-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.help-text {
  margin: 5px 0 0 0;
  font-size: 12px;
  color: #999;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  background: #f0f0f0;
  color: #333;
}

.cancel-btn:hover {
  background: #e0e0e0;
}

.confirm-btn {
  background: #1890ff;
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background: #40a9ff;
}
</style>