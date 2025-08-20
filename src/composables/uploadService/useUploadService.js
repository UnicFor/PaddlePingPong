import { ref, computed } from 'vue'
import { ChunkProcessor } from '@/utils/chunkProcessor.js'
import { UploadQueue } from '@/utils/uploadQueue.js'
import { useUploadStore } from '@/stores/upload.js'
import request from '@/utils/request.js'

export function useUploadService() {
    const uploadStore = useUploadStore()
    
    // 本地状态
    const statusMessage = ref('')
    const statusClass = ref('')

    const isDevMode = computed(() => uploadStore.isDevMode)
    
    // 核心服务
    const chunkProcessor = new ChunkProcessor(5 * 1024 * 1024)
    const uploadQueue = new UploadQueue(isDevMode ? 2 : 4)
    
    
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
        const speed = `${((data.completed / data.total) * currentFile.size / ((Date.now() - startTime) / 1000) / (1024 * 1024)).toFixed(2)} MB/s`

        uploadStore.updateProgress({
            progress: data.progress,
            speed: speed,
            time: '计算中...',
            chunkInfo: isDevMode.value ? data.chunkInfo : null
        })
        
        if (isDevMode.value) {
            console.log(`⏳ 总体进度: ${data.progress.toFixed(1)}% (${data.completed}/${data.total} 分片)`)
        }
    }
    
    uploadQueue.onComplete = async (results) => {
        try {
            if (isDevMode.value) {
                console.log('🎯 所有分片上传完成，开始合并...')
                console.log('📋 分片详情:', results.map(r => ({
                    index: r.chunkIndex,
                    size: r.size,
                    id: r.id
                })))
            }

            // 合并分片
            if (!isDevMode.value) {
                await mergeChunks()
            } else {
                // 开发者模式模拟合并
                console.log('🔧 开发者模式：模拟分片合并...')
                await new Promise(resolve => setTimeout(resolve, 2000))
                console.log('✅ 模拟合并完成')
            }
            
            // 完成上传
            uploadStore.completeUpload({
                id: results[0]?.id || 'uploaded',
                filename: currentFile.name,
                size: currentFile.size
            })
            
            statusMessage.value = '文件已经上传完毕，请耐心等待系统进行处理'
            statusClass.value = 'success'
            
            // 显示完成弹窗
            setTimeout(() => {
                alert('文件已经上传完毕，请耐心等待系统进行处理')
            }, 100)
            
        } catch (error) {
            uploadStore.cancelUpload()
            statusMessage.value = `上传失败: ${error.message}`
            statusClass.value = 'error'
        }
    }
    
    uploadQueue.onError = (error, task) => {
        uploadStore.cancelUpload()
        statusMessage.value = `上传失败: ${error.message}`
        statusClass.value = 'error'

        if (isDevMode.value) {
            console.error('❌ 分片上传失败:', {
                chunkIndex: task.chunkData?.index,
                error: error.message,
                retryCount: task.retryCount
            })
        }
    }
    
    // 上传分片
    const uploadChunk = async (chunkData, abortSignal) => {

        if (isDevMode.value) {
            // 开发者模式模拟上传
            console.log(`🧪 开发者模式：模拟上传分片 ${chunkData.index + 1}/${chunkData.totalChunks}`)
            
            // 模拟网络延迟
            const delay = Math.random() * 800 + 200
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(resolve, delay)
                abortSignal?.addEventListener('abort', () => {
                    clearTimeout(timeout)
                    reject(new Error('上传已取消'))
                })
            })
            
            // 检查是否已取消
            if (abortSignal?.aborted) {
                throw new Error('上传已取消')
            }
            
            // 模拟随机失败（2%概率）
            if (Math.random() < 0.02 && chunkData.retryCount < 3) {
                console.log(`⚠️ 模拟网络错误：分片 ${chunkData.index + 1}`)
                throw new Error('模拟网络错误')
            }
            
            return {
                id: `chunk-${chunkData.index}`,
                index: chunkData.index,
                size: chunkData.size,
                uploaded: true
            }
        }

        // 生产环境上传
        const formData = new FormData()
        const chunkBlob = chunkData.chunk
        // 验证chunk是否有效
        if (!chunkBlob || chunkBlob.size === 0) {
            throw new Error(`分片 ${chunkData.index} 为空`)
        }

        formData.append('chunk', chunkBlob, `chunk_${chunkData.index}`);
        formData.append('index', chunkData.index)
        formData.append('totalChunks', chunkData.totalChunks)
        formData.append('hash', chunkData.hash)
        formData.append('filename', chunkData.file.name)
        
        // 调试日志
        console.log(`📤 发送分片 ${chunkData.index}:`, {
            blobSize: chunkBlob.size,
            hash: chunkData.hash?.substring(0, 16) + '...',
            filename: chunkData.file?.name
        })

        try {
            const response = await request.post('/api/upload/chunk', formData, {
                signal: abortSignal,
                timeout: 10000 // 10秒超时
            });
            
            return response.data
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('上传已取消')
            }
            throw new Error(error.response?.data?.message || `上传失败: ${error.message}`)
        }
    }
    
    // 合并分片
    const mergeChunks = async () => {
        try {
            const response = await request.post('/api/upload/merge', {
                filename: currentFile.name,
                totalChunks: totalChunksCount
            })
            
            return response.data
        } catch (error) {
            throw new Error(error.response?.data?.message || '合并分片失败')
        }
    }
    // 断点续传检查
    const checkResumeStatus = async (file) => {
        if (isDevMode.value) {
            console.log('🔍 开发者模式：检查断点续传状态...')
            return { uploadedChunks: [], canResume: false, totalChunks: 0 }
        }
        
        try {
            const response = await request.post('/api/upload/status', {
                filename: file.name,
                size: file.size
            })
            
            return {
                uploadedChunks: response.data.uploadedChunks || [],
                canResume: response.data.canResume || false,
                totalChunks: response.data.totalChunks || 0
            }
        } catch (error) {
            console.error('断点续传检查失败:', error)
            return { uploadedChunks: [], canResume: false, totalChunks: 0 }
        }
    }
    
    // 开始上传
    const startUpload = async (file) => {
        if (!file) throw new Error('请选择文件')
        
        // 检查是否可以上传
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
            // 检查断点续传状态
            const resumeStatus = await checkResumeStatus(file)
            
            // 使用异步生成器获取包含hash的chunk数据
            const chunks = []
            for await (const chunkData of chunkProcessor.generateChunks(file)) {
                chunks.push(chunkData)
            }
            totalChunksCount = chunks.length

            // 过滤已上传的分片（断点续传）
            let pendingChunks = chunks
            if (resumeStatus.canResume && resumeStatus.uploadedChunks.length > 0) {
                pendingChunks = chunks.filter(chunk => 
                    !resumeStatus.uploadedChunks.includes(chunk.index)
                )
                console.log(`📋 断点续传：跳过 ${resumeStatus.uploadedChunks.length} 个已上传分片`)
            }
            
            console.log(`📊 总需上传分片: ${pendingChunks.length}/${chunks.length}`)
            
            if (pendingChunks.length === 0) {
                // 所有分片都已上传，直接合并
                console.log('✅ 所有分片已上传，开始合并...')
                uploadQueue.onComplete([])
                return
            }
            
            // 设置总任务数
            uploadQueue.totalTasks = pendingChunks.length
            
            // 添加分片到上传队列
            for (const chunk of pendingChunks) {
                uploadQueue.addTask(chunk, uploadChunk)
            }
            
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
        statusMessage.value = '上传已取消'
        statusClass.value = 'error'
        
        if (isDevMode.value) {
            console.log('✅ 上传任务已完全取消')
            console.log('📊 取消后状态:', {
                activeTasks: uploadQueue.activeUploads.size,
                pendingTasks: uploadQueue.queue.length,
                completedTasks: uploadQueue.completedUploads.size,
                isCancelled: uploadQueue.isCancelled
            })
        }
    }
    
    // 恢复上传状态
    const resumeUpload = () => {
        if (uploadStore.isUploading && uploadStore.currentFile) {
            currentFile = uploadStore.currentFile
            startTime = Date.now() - (uploadStore.progress / 100) * (uploadStore.currentFile.size / 1024 / 1024 / 2)
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
        cancelUpload,
        resumeUpload
    }
}