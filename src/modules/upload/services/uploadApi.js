// src/modules/upload/services/uploadApi.js
import request from '@/utils/request.js'
import { API_ENDPOINTS } from './uploadConstants.js'
import { PROD_MODE_CONFIG } from './uploadConstants.js'

// 开发者模式模拟响应
const createDevResponse = (data) => ({
    data: {
        id: `chunk-${data.index}`,
        index: data.index,
        size: data.size,
        uploaded: true
    }
})

// 上传分片
export const uploadChunkApi = async (chunkData, abortSignal) => {
    const formData = new FormData()
    formData.append('chunk', chunkData.chunk, `chunk_${chunkData.index}`)
    formData.append('index', chunkData.index)
    formData.append('totalChunks', chunkData.totalChunks)
    formData.append('hash', chunkData.hash)
    formData.append('filename', chunkData.file.name)

    console.log(`📤 发送分片 ${chunkData.index}:`, {
        blobSize: chunkData.chunk.size,
        hash: chunkData.hash?.substring(0, 16) + '...',
        filename: chunkData.file?.name
    })

    const response = await request.post(API_ENDPOINTS.CHUNK_UPLOAD, formData, {
        signal: abortSignal,
        timeout: PROD_MODE_CONFIG.TIMEOUT
    })
    
    return response.data
}

// 合并分片
export const mergeChunksApi = async (filename, totalChunks) => {
    const response = await request.post(API_ENDPOINTS.CHUNK_MERGE, {
        filename,
        totalChunks
    })
    return response.data
}

// 检查断点续传状态 - 简化参数
export const checkResumeStatusApi = async (file) => {
    const response = await request.post(API_ENDPOINTS.UPLOAD_STATUS, {
        filename: file.name,
        size: file.size
    })
    
    return {
        uploadedChunks: response.data.uploadedChunks || [],
        canResume: response.data.canResume || false,
        totalChunks: response.data.totalChunks || 0
    }
}