// src/modules/upload/services/uploadHelpers.js
import { DEV_MODE_CONFIG } from './uploadConstants.js'

// 开发者模式：模拟网络延迟
export const simulateNetworkDelay = (signal) => {
    const delay = Math.random() * DEV_MODE_CONFIG.SIMULATE_DELAY_MAX + DEV_MODE_CONFIG.SIMULATE_DELAY_MIN
    
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(resolve, delay)
        signal?.addEventListener('abort', () => {
            clearTimeout(timeout)
            reject(new Error('上传已取消'))
        })
    })
}

// 开发者模式：模拟随机失败
export const shouldSimulateFailure = () => {
    return Math.random() < DEV_MODE_CONFIG.SIMULATE_FAILURE_RATE
}

// 计算上传速度
export const calculateUploadSpeed = (completed, total, fileSize, startTime) => {
    const elapsedSeconds = (Date.now() - startTime) / 1000
    const uploadedBytes = (completed / total) * fileSize
    const speedMBps = uploadedBytes / elapsedSeconds / (1024 * 1024)
    return `${speedMBps.toFixed(2)} MB/s`
}

// 格式化调试日志
export const formatDebugLog = (type, data) => {
    switch (type) {
        case 'progress':
            return `⏳ 总体进度: ${data.progress.toFixed(1)}% (${data.completed}/${data.total} 分片)`
        
        case 'complete':
            return {
                title: '🎯 所有分片上传完成，开始合并...',
                details: data.map(r => ({
                    index: r.chunkIndex,
                    size: r.size,
                    id: r.id
                }))
            }
        
        case 'cancel':
            return {
                activeTasks: data.activeUploads.size,
                pendingTasks: data.queue.length,
                completedTasks: data.completedUploads.size,
                isCancelled: data.isCancelled
            }
        
        case 'error':
            return {
                chunkIndex: data.chunkData?.index,
                error: data.error.message,
                retryCount: data.retryCount
            }
    }
}

// 验证文件有效性
export const validateFile = (file) => {
    if (!file) throw new Error('请选择文件')
    return true
}

// 验证chunk有效性
export const validateChunk = (chunkBlob, index) => {
    if (!chunkBlob || chunkBlob.size === 0) {
        throw new Error(`分片 ${index} 为空`)
    }
    return true
}