import { ref, computed, onUnmounted } from 'vue'
import { useUploadStore } from '@/stores/upload.js'
import { WorkerManager } from '@/workers/workerManager.js'
import { ChunkProcessor } from '@/utils/chunkProcessor.js'
import request from '@/utils/request.js'
import Worker from '@/workers/fileUpload.worker.js?worker'

export function useWorkerUploadService() {
    const uploadStore = useUploadStore()
    
    // 本地状态 - 移除未使用的变量
    const statusMessage = ref('')
    const statusClass = ref('')
    const workerManager = ref(null)
    
    // 核心服务
    const chunkProcessor = new ChunkProcessor(5 * 1024 * 1024)
    
    let currentFile = null
    let startTime = 0
    let totalChunksCount = 0
    
    // 使用全局状态
    const progress = computed(() => uploadStore.progress)
    const uploadSpeed = computed(() => uploadStore.uploadSpeed)
    const estimatedTime = computed(() => uploadStore.estimatedTime)
    const isUploading = computed(() => uploadStore.isUploading)
    const isDevMode = computed(() => uploadStore.isDevMode)
    
    // 初始化Worker管理器
    const initWorkerManager = () => {
    if (!workerManager.value) {
        const worker = new Worker()
        workerManager.value = new WorkerManager(worker)
        workerManager.value.setupMessageHandler()
    }
}
    
    // 终止Worker
    const terminateWorker = () => {
        if (workerManager.value) {
            workerManager.value.terminate()
            workerManager.value = null
        }
    }
    
    // 清理资源
    onUnmounted(() => {
        terminateWorker()
    })
    
    // 上传单个分片（通过Worker）
    const uploadChunkViaWorker = async (chunkData) => {
        if (!workerManager.value) {
            throw new Error('Worker管理器未初始化')
        }
        
        const uploadConfig = {
            url: '/api/upload/chunk',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('jwt') || ''}`
            }
        }
        
        try {
            const result = await workerManager.value.uploadChunk({
                chunkData,
                uploadConfig
            })
            return result
        } catch (error) {
            throw new Error(`Worker上传失败: ${error.message}`)
        }
    }
    
    // 流式上传（通过Worker）- 修复接口不一致问题
    const uploadStreamViaWorker = async (file) => {
        if (!workerManager.value) {
            throw new Error('Worker管理器未初始化')
        }
        
        const uploadConfig = {
            url: '/api/upload/chunk',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('jwt') || ''}`
            }
        }
        
        return new Promise((resolve, reject) => {
            const chunks = []
            let uploadedCount = 0
            
            // 使用WorkerManager的消息处理
            const originalHandler = workerManager.value.worker.onmessage
            
            workerManager.value.worker.onmessage = (event) => {
                const { type, taskId, result, error, ...data } = event.data
                
                switch (type) {
                    case 'STREAM_PROGRESS':
                        uploadedCount++
                        const currentProgress = (uploadedCount / data.totalChunks) * 100
                        
                        // 计算速度和时间
                        const elapsed = (Date.now() - startTime) / 1000
                        const speed = file.size * (uploadedCount / data.totalChunks) / elapsed / (1024 * 1024)
                        const remainingBytes = file.size * (1 - uploadedCount / data.totalChunks)
                        const remainingTime = remainingBytes / (speed * 1024 * 1024)
                        
                        uploadStore.updateProgress({
                            progress: currentProgress,
                            speed: `${speed.toFixed(2)} MB/s`,
                            time: formatTime(remainingTime),
                            chunkInfo: isDevMode.value ? {
                                index: data.chunkIndex,
                                totalChunks: data.totalChunks
                            } : null
                        })
                        
                        if (isDevMode.value) {
                            console.log(`⏳ Worker流式上传: ${currentProgress.toFixed(1)}% (${uploadedCount}/${data.totalChunks})`)
                        }
                        break
                        
                    case 'CHUNK_UPLOADED':
                        chunks.push(result)
                        break
                        
                    case 'UPLOAD_COMPLETE':
                        resolve(chunks)
                        break
                        
                    case 'CHUNK_ERROR':
                        reject(new Error(error))
                        break
                        
                    default:
                        if (originalHandler) {
                            originalHandler(event)
                        }
                }
            }
            
            // 启动Worker流式上传
            workerManager.value.worker.postMessage({
                type: 'STREAM_UPLOAD',
                data: {
                    file,
                    uploadConfig
                }
            })
        })
    }
    
    // 格式化时间显示
    const formatTime = (seconds) => {
        if (seconds < 60) return `${Math.ceil(seconds)}秒`
        if (seconds < 3600) return `${Math.ceil(seconds / 60)}分钟`
        return `${Math.ceil(seconds / 3600)}小时`
    }
    
    // 断点续传检查
    const checkResumeStatus = async (file) => {
        if (isDevMode.value) {
            console.log('🔍 Worker模式：检查断点续传状态...')
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
            console.error('Worker断点续传检查失败:', error)
            return { uploadedChunks: [], canResume: false, totalChunks: 0 }
        }
    }
    
    // 合并分片
    const mergeChunks = async () => {
        try {
            const response = await request.post('/api/upload/merge', {
                filename: currentFile.name,
                totalChunksCount: totalChunksCount
            })
            return response.data
        } catch (error) {
            throw new Error(error.response?.data?.message || '合并分片失败')
        }
    }
    
    // 开发者模式模拟上传（Worker版）
    const simulateWorkerUpload = async (file) => {
        console.log('🧪 Worker开发者模式：模拟上传...')
        
        const chunks = []
        let uploadedCount = 0
        
        const totalChunks = Math.ceil(file.size / chunkProcessor.chunkSize)
        
        for (let i = 0; i < totalChunks; i++) {
            chunks.push({
                id: `worker-chunk-${i}`,
                index: i,
                size: Math.min(chunkProcessor.chunkSize, file.size - i * chunkProcessor.chunkSize),
                uploaded: true
            })
            
            uploadedCount++
            const progress = (uploadedCount / totalChunks) * 100
            
            // 计算速度和时间
            const elapsed = (Date.now() - startTime) / 1000
            const speed = (file.size * (uploadedCount / totalChunks)) / elapsed / (1024 * 1024)
            const remainingBytes = file.size * (1 - uploadedCount / totalChunks)
            const remainingTime = remainingBytes / (speed * 1024 * 1024)
            
            uploadStore.updateProgress({
                progress: progress,
                speed: `${speed.toFixed(2)} MB/s`,
                time: formatTime(remainingTime),
                chunkInfo: isDevMode.value ? {
                    index: i,
                    totalChunks: totalChunks
                } : null
            })
            
            // 模拟网络延迟
            await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200))
            
            // 模拟随机失败（低概率）
            if (Math.random() < 0.01) {
                throw new Error('模拟Worker网络错误')
            }
        }
        
        return chunks
    }
    
    // 开始上传（Worker版本）- 修复状态管理
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
        
        await uploadStore.startUpload(file)
        initWorkerManager()
        
        try {
            statusMessage.value = '正在准备上传...'
            statusClass.value = 'info'
            
            // 检查断点续传状态
            const resumeStatus = await checkResumeStatus(file)
            
            // 获取分片数据
            const chunks = []
            for await (const chunkData of chunkProcessor.generateChunks(file)) {
                chunks.push(chunkData)
            }
            totalChunksCount = chunks.length
            
            // 过滤已上传的分片
            let pendingChunks = chunks
            if (resumeStatus.canResume && resumeStatus.uploadedChunks.length > 0) {
                pendingChunks = chunks.filter(chunk => 
                    !resumeStatus.uploadedChunks.includes(chunk.index)
                )
                console.log(`📋 Worker断点续传：跳过 ${resumeStatus.uploadedChunks.length} 个已上传分片`)
            }
            
            console.log(`📊 Worker总需上传分片: ${pendingChunks.length}/${chunks.length}`)
            
            if (pendingChunks.length === 0) {
                // 所有分片都已上传，直接合并
                console.log('✅ Worker所有分片已上传，开始合并...')
                await handleUploadComplete([])
                return
            }
            
            // 根据分片数量选择上传策略
            let results = []
            
            if (isDevMode.value) {
                // 开发者模式：模拟上传
                results = await simulateWorkerUpload(file)
            } else if (pendingChunks.length > 20) {
                // 大文件：使用流式Worker上传
                console.log('🌊 使用Worker流式上传...')
                results = await uploadStreamViaWorker(file)
            } else {
                // 小文件：逐个分片Worker上传
                console.log('📦 使用Worker分片上传...')
                
                for (let i = 0; i < pendingChunks.length; i++) {
                    const chunk = pendingChunks[i]
                    const result = await uploadChunkViaWorker(chunk)
                    results.push(result)
                    
                    // 更新进度
                    const progress = ((i + 1) / pendingChunks.length) * 100
                    const uploadedSize = (i + 1) * chunk.size
                    const elapsed = (Date.now() - startTime) / 1000
                    const speed = uploadedSize / elapsed / (1024 * 1024)
                    const remainingBytes = (pendingChunks.length - i - 1) * chunk.size
                    const remainingTime = remainingBytes / (speed * 1024 * 1024)
                    
                    uploadStore.updateProgress({
                        progress: progress,
                        speed: `${speed.toFixed(2)} MB/s`,
                        time: formatTime(remainingTime),
                        chunkInfo: isDevMode.value ? {
                            index: chunk.index,
                            totalChunks: totalChunksCount
                        } : null
                    })
                    
                    if (isDevMode.value) {
                        console.log(`📤 Worker分片 ${i+1}/${pendingChunks.length} 完成`)
                    }
                }
            }
            
            // 处理上传完成
            await handleUploadComplete(results)
            
        } catch (error) {
            uploadStore.handleError(error)
            statusMessage.value = `Worker上传失败: ${error.message}`
            statusClass.value = 'error'
            throw error
        }
    }
    
    // 处理上传完成
    const handleUploadComplete = async (results) => {
        try {
            statusMessage.value = '正在合并分片...'
            statusClass.value = 'info'
            
            if (isDevMode.value) {
                console.log('🎯 Worker所有分片上传完成，开始合并...')
            }
            
            // 合并分片
            if (!isDevMode.value) {
                await mergeChunks()
            } else {
                // 开发者模式模拟合并
                console.log('🔧 Worker开发者模式：模拟分片合并...')
                await new Promise(resolve => setTimeout(resolve, 1500))
            }
            
            // 完成上传
            uploadStore.completeUpload({
                id: results[0]?.id || `worker-upload-${Date.now()}`,
                filename: currentFile.name,
                size: currentFile.size
            })
            
            statusMessage.value = 'Worker上传完成，请耐心等待系统处理'
            statusClass.value = 'success'
            
            // 清理Worker
            setTimeout(() => {
                terminateWorker()
            }, 3000)
            
        } catch (error) {
            uploadStore.cancelUpload()
            statusMessage.value = `Worker上传失败: ${error.message}`
            statusClass.value = 'error'
            throw error
        }
    }
    
    // 取消上传 - 修复状态管理
    const cancelUpload = () => {
        console.log('🛑 正在取消Worker上传任务...')
        
        statusMessage.value = '正在取消上传...'
        statusClass.value = 'warning'
        
        if (workerManager.value) {
            workerManager.value.worker.postMessage({ type: 'CANCEL_UPLOAD' })
            setTimeout(() => {
                terminateWorker()
            }, 500)
        }
        
        uploadStore.cancelUpload()
        statusMessage.value = 'Worker上传已取消'
        statusClass.value = 'error'
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