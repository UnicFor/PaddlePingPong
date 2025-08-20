<script setup>
import { useUploadService } from '@/composables/uploadService/useUploadService'
import { useWorkerUploadService } from '@/composables/uploadService/useWorkerUploadService'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  file: {
    type: File,
    default: null
  },
  title: {
    type: String,
    default: '上传文件'
  }
})

const emit = defineEmits(['close', 'uploaded', 'error'])

// 使用全局状态
const {
  progress,
  uploadSpeed,
  estimatedTime,
  isUploading,
  statusMessage,
  statusClass,
  startUpload: serviceStartUpload,
  cancelUpload: serviceCancelUpload
} = useUploadService()

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 开始上传
const startUpload = async () => {
  try {
    await serviceStartUpload(props.file)
  } catch (error) {
    console.error('上传失败:', error)
  }
}

// 取消上传
const handleCancel = async () => {
  try {
    if (confirm('确定要取消上传吗？')) {
      await serviceCancelUpload()
    }
  } catch (error) {
    console.error('取消上传失败:', error)
  }
}

// 关闭面板
const handleClose = () => {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="upload-panel-overlay" @click.self="handleClose">
      <div class="upload-panel">
        <div class="panel-header">
          <h3>{{ title }}</h3>
          <button class="close-btn" @click="handleClose">×</button>
        </div>

        <div class="panel-content">
          <!-- 文件信息 -->
          <div v-if="file" class="file-info">
            <div class="file-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="#42b983"/>
              </svg>
            </div>
            <div class="file-details">
              <h4>{{ file.name }}</h4>
              <p>{{ formatFileSize(file.size) }} • {{ file.type }}</p>
            </div>
          </div>

          <!-- 上传进度 -->
          <div v-if="isUploading" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <div class="progress-info">
              <span>{{ progress.toFixed(2) }}%</span>
              <span>{{ uploadSpeed }}</span>
              <span>{{ estimatedTime }}</span>
            </div>
          </div>

          <!-- 状态信息 -->
          <div v-if="statusMessage" :class="['status-message', statusClass]">
            {{ statusMessage }}
          </div>

          <!-- 操作按钮 -->
          <div class="panel-actions">
            <button 
              v-if="!isUploading" 
              class="upload-btn" 
              @click="startUpload"
              :disabled="!file"
            >
              开始上传
            </button>
            <button 
              v-if="isUploading" 
              class="cancel-btn" 
              @click="handleCancel"
              :disabled="!isUploading"
            >
              取消上传
            </button>
            <button 
              class="close-action-btn" 
              @click="handleClose"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.upload-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.upload-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: 400px;
  max-width: 90%;
  max-height: 80vh;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1.5rem;
  border-bottom: 1px solid #eee;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.panel-content {
  padding: 1.5rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.file-details h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
}

.file-details p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.upload-progress {
  margin-bottom: 1.5rem;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #42b983;
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.status-message {
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  text-align: center;
}

.status-message.success {
  background: #e8f5e8;
  color: #2d7d2d;
}

.status-message.error {
  background: #fee;
  color: #c33;
}

.panel-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.upload-btn, .cancel-btn, .close-action-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.upload-btn {
  background: #42b983;
  color: white;
}

.cancel-btn {
  background: #ff4757;
  color: white;
}

.close-action-btn {
  background: #eee;
  color: #333;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>