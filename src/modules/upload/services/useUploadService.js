// src/modules/upload/services/useUploadService.js
import { ref, computed } from 'vue'
import { ChunkProcessor } from '@/modules/upload/utils/chunkProcessor.js'
import { UploadQueue } from '@/modules/upload/utils/uploadQueue.js'
import { useUploadStore } from '@/stores/upload.js'
import { uploadChunkApi, mergeChunksApi, checkResumeStatusApi } from './uploadApi.js'
import { 
    calculateUploadSpeed, 
    simulateNetworkDelay, 
    shouldSimulateFailure,
    formatDebugLog,
    validateFile,
    validateChunk 
} from './uploadHelpers.js'
import { DEV_MODE_CONFIG, PROD_MODE_CONFIG, STATUS_MESSAGES } from './uploadConstants.js'

export function useUploadService() {
    const uploadStore = useUploadStore()
    
    // 本地状态
    const statusMessage = ref('')
    const statusClass = ref('')

    const isDevMode = computed(() => uploadStore.isDevMode)
    
    // 核心服务
    const chunkSize = isDevMode.value ? DEV_MODE_CONFIG.CHUNK_SIZE : PROD_MODE_CONFIG.CHUNK_SIZE
    const maxConcurrency = isDevMode.value ? DEV_MODE_CONFIG.MAX_CONCURRENCY : PROD_MODE_CONFIG.MAX_CONCURRENCY
    
    const chunkProcessor = new ChunkProcessor(chunkSize)
    const uploadQueue = new UploadQueue(maxConcurrency)
    
    let currentFile = null
    let startTime = 0
    let totalChunksCount = 0 
    
    // 使用全局状态
    const progress = computed(() => uploadStore.progress)
    const uploadSpeed = computed(() => uploadStore.uploadSpeed)
    const estimatedTime = computed(() => uploadStore.estimatedTime)
    const isUploading = computed(() => uploadStore.isUploading)
    
    // 设置队列回调
    uploadQueue.onProgress = (data) => {
        const speed = calculateUploadSpeed(
            data.completed, 
            data.total, 
            currentFile.size, 
            startTime
        )

        uploadStore.updateProgress({
            progress: data.progress,
            speed: speed,
            time: '计算中...',
            chunkInfo: isDevMode.value ? data.chunkInfo : null
        })
        
        if (isDevMode.value) {
            console.log(formatDebugLog('progress', data))
        }
    }
    
    uploadQueue.onComplete = async (results) => {
        try {
            if (isDevMode.value) {
                const log = formatDebugLog('complete', results)
                console.log(log.title)
                console.log('📋 分片详情:', log.details)
            }

            // 合并分片
            if (!isDevMode.value) {
                await mergeChunksApi(currentFile.name, totalChunksCount)
            } else {
                console.log('🔧 开发者模式：模拟分片合并...')
                await new Promise(resolve => setTimeout(resolve, DEV_MODE_CONFIG.MERGE_DELAY))
                console.log('✅ 模拟合并完成')
            }
            
            // 完成上传
            uploadStore.completeUpload({
                id: results[0]?.id || 'uploaded',
                filename: currentFile.name,
                size: currentFile.size
            })
            
            statusMessage.value = STATUS_MESSAGES.SUCCESS
            statusClass.value = 'success'
            
            setTimeout(() => {
                alert(STATUS_MESSAGES.SUCCESS)
            }, 100)
            
        } catch (error) {
            uploadStore.cancelUpload()
            statusMessage.value = `${STATUS_MESSAGES.ERROR_PREFIX}${error.message}`
            statusClass.value = 'error'
        }
    }
    
    uploadQueue.onError = (error, task) => {
        uploadStore.cancelUpload()
        statusMessage.value = `${STATUS_MESSAGES.ERROR_PREFIX}${error.message}`
        statusClass.value = 'error'

        if (isDevMode.value) {
            console.error('❌ 分片上传失败:', formatDebugLog('error', { chunkData: task.chunkData, error, retryCount: task.retryCount }))
        }
    }
    
    // 上传分片
    const uploadChunk = async (chunkData, abortSignal) => {
        if (isDevMode.value) {
            await simulateNetworkDelay(abortSignal)
            
            if (abortSignal?.aborted) throw new Error('上传已取消')
            if (shouldSimulateFailure() && chunkData.retryCount < 3) {
                throw new Error('模拟网络错误')
            }
            
            return {
                id: `chunk-${chunkData.index}`,
                index: chunkData.index,
                size: chunkData.size,
                uploaded: true
            }
        }

        validateChunk(chunkData.chunk, chunkData.index)
        return await uploadChunkApi(chunkData, abortSignal)
    }
    
    // 开始上传
    const startUpload = async (file) => {
        validateFile(file)
        
        if (!uploadStore.canUpload) {
            if (uploadStore.serverStatus === 'disconnected') {
                throw new Error('无法连接到服务器，请检查网络连接')
            }
            throw new Error('当前无法上传文件')
        }
        
        currentFile = file
        startTime = Date.now()
        
        uploadQueue.reset()
        await uploadStore.startUpload(file)
        
        try {
            const resumeStatus = isDevMode.value 
                ? { uploadedChunks: [], canResume: false, totalChunks: 0 }
                : await checkResumeStatusApi(file)
            
            const chunks = []
            for await (const chunkData of chunkProcessor.generateChunks(file)) {
                chunks.push(chunkData)
            }
            totalChunksCount = chunks.length

            let pendingChunks = chunks
            if (resumeStatus.canResume && resumeStatus.uploadedChunks.length > 0) {
                pendingChunks = chunks.filter(chunk => 
                    !resumeStatus.uploadedChunks.includes(chunk.index)
                )
                
                if (isDevMode.value) {
                    console.log(`📋 断点续传：跳过 ${resumeStatus.uploadedChunks.length} 个已上传分片`)
                }
            }
            
            if (isDevMode.value) {
                console.log(`📊 总需上传分片: ${pendingChunks.length}/${chunks.length}`)
            }
            
            if (pendingChunks.length === 0) {
                if (isDevMode.value) console.log('✅ 所有分片已上传，开始合并...')
                uploadQueue.onComplete([])
                return
            }
            
            uploadQueue.totalTasks = pendingChunks.length
            pendingChunks.forEach(chunk => {
                uploadQueue.addTask(chunk, uploadChunk)
            })
            
        } catch (error) {
            uploadStore.handleError(error)
            throw error
        }
    }
    
    // 取消上传
    const cancelUpload = () => {
        console.log('🛑 正在取消上传任务...')
        
        uploadQueue.cancelAll()
        uploadStore.cancelUpload()
        statusMessage.value = STATUS_MESSAGES.CANCELLED
        statusClass.value = 'error'
        
        if (isDevMode.value) {
            console.log('✅ 上传任务已完全取消')
            console.log('📊 取消后状态:', formatDebugLog('cancel', uploadQueue))
        }
    }
    
    return {
        progress,
        uploadSpeed,
        estimatedTime,
        isUploading,
        statusMessage,
        statusClass,
        startUpload,
        cancelUpload
    }
}