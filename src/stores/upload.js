import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUploadStore = defineStore('upload', () => {
    const isDevMode = import.meta.env.MODE === 'development'
    const serverStatus = ref('checking') // checking, connected, disconnected

    // 状态
    const isUploading = ref(false)
    const currentFile = ref(null)
    const progress = ref(0)
    const uploadSpeed = ref('0 MB/s')
    const estimatedTime = ref('00:00')
    const uploadedFile = ref(null)

    
    // 计算属性
    const hasActiveUpload = computed(() => isUploading.value && currentFile.value !== null)
    const canUpload = computed(() => serverStatus.value === 'connected' || isDevMode)
    
    // 检查服务器连接
    const checkServerConnection = async () => {
        if (isDevMode) {
            serverStatus.value = 'connected'
            return true
        }
        
        try {
            const response = await fetch('/api/health', {
                method: 'GET',
                signal: AbortSignal.timeout(3000)
            })
            serverStatus.value = response.ok ? 'connected' : 'disconnected'
            return response.ok
        } catch (error) {
            console.error('服务器连接检查失败:', error)
            serverStatus.value = 'disconnected'
            return false
        }
    }
    
    // 开始上传
    const startUpload = async (file) => {
        // 检查服务器连接
        const isConnected = await checkServerConnection()
        if (!isConnected && !isDevMode) {
            throw new Error('无法连接到服务器，请检查网络连接')
        }
        
        isUploading.value = true
        currentFile.value = file
        progress.value = 0
        uploadSpeed.value = '0 MB/s'
        estimatedTime.value = '计算中...'
        
        if (isDevMode) {
            console.log('🚀 开发者模式：开始上传文件', {
                name: file.name,
                size: file.size,
                type: file.type
            })
        }
    }
    
    // 更新进度
    const updateProgress = ({ progress: newProgress, speed, time, chunkInfo }) => {
        progress.value = Number(newProgress).toFixed(2) || 0
        uploadSpeed.value = speed
        estimatedTime.value = time
        
        if (isDevMode && chunkInfo) {
            console.log('📊 分片上传进度:', {
                chunkIndex: chunkInfo.index,
                totalChunks: chunkInfo.totalChunks,
                progress: `${Number(newProgress).toFixed(2)}%`,
                speed: speed,
                chunkSize: chunkInfo.size
            })
        }
    }
    
    // 完成上传
    const completeUpload = (fileInfo) => {
        isUploading.value = false
        uploadedFile.value = fileInfo
        currentFile.value = null
        
        if (isDevMode) {
            console.log('✅ 上传完成:', fileInfo)
        }
        
        // 延迟重置状态，让用户看到完成消息
        setTimeout(() => {
            uploadedFile.value = null
            progress.value = 0
            uploadSpeed.value = '0 MB/s'
            estimatedTime.value = '00:00'
        }, 3000)
    }
    
    // 取消上传
    const cancelUpload = () => {
        isUploading.value = false
        currentFile.value = null
        progress.value = 0
        uploadSpeed.value = '0 MB/s'
        estimatedTime.value = '00:00'
        
        if (isDevMode) {
            console.log('❌ 上传已取消')
        }
    }
    
    // 错误处理
    const handleError = (error) => {
        isUploading.value = false
        currentFile.value = null
        
        if (isDevMode) {
            console.error('❌ 上传错误:', error)
        }
    }
    
    // 重置状态
    const reset = () => {
        isUploading.value = false
        currentFile.value = null
        progress.value = 0
        uploadSpeed.value = '0 MB/s'
        estimatedTime.value = '00:00'
        uploadedFile.value = null
        serverStatus.value = 'checking'
    }
    
    return {
        // 状态
        isUploading,
        currentFile,
        progress,
        uploadSpeed,
        estimatedTime,
        uploadedFile,
        isDevMode,
        serverStatus,
        canUpload,
        
        // 计算属性
        hasActiveUpload,
        
        // 方法
        checkServerConnection,
        startUpload,
        updateProgress,
        completeUpload,
        cancelUpload,
        handleError,
        reset
    }
})