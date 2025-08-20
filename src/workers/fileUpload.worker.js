import { ChunkProcessor } from '../utils/chunkProcessor.js'

class UploadWorker {
    constructor() {
        this.chunkProcessor = new ChunkProcessor()
        this.activeUploads = new Map()
    }

    // 处理上传任务
    async handleChunkUpload(data) {
        const { chunkData, uploadConfig } = data
        const { url, headers } = uploadConfig

        const formData = new FormData()
        formData.append('chunk', chunkData.chunk)
        formData.append('index', chunkData.index)
        formData.append('totalChunks', chunkData.totalChunks)
        formData.append('hash', chunkData.hash)
        formData.append('filename', chunkData.file.name)

        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                ...headers,
                'Content-Range': `bytes ${chunkData.start}-${chunkData.end - 1}/${chunkData.file.size}`
            }
        })

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
    }

    async handleStreamUpload(data) {
        const { file, uploadConfig } = data
        const chunks = []

        for await (const chunkData of this.chunkProcessor.generateChunks(file)) {
            const result = await this.handleChunkUpload({
                chunkData,
                uploadConfig
            })
            
            chunks.push(result)
            
            // 发送进度更新
            self.postMessage({
                type: 'STREAM_PROGRESS',
                progress: (chunks.length / chunkData.totalChunks) * 100,
                chunkIndex: chunkData.index,
                totalChunks: chunkData.totalChunks
            })
        }

        return chunks
    }
}

// Worker 消息处理
const uploadWorker = new UploadWorker()

self.onmessage = async function(event) {
    const { type, taskId, data } = event.data

    try {
        let result
        
        switch (type) {
            case 'UPLOAD_CHUNK':
                result = await uploadWorker.handleChunkUpload(data)
                break
            case 'STREAM_UPLOAD':
                result = await uploadWorker.handleStreamUpload(data)
                break
            default:
                throw new Error('未知的消息类型')
        }

        self.postMessage({
            type: 'CHUNK_UPLOADED',
            taskId,
            result
        })
        
    } catch (error) {
        self.postMessage({
            type: 'CHUNK_ERROR',
            taskId,
            error: error.message
        })
    }
}