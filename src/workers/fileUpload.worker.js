import { ChunkProcessor } from '../utils/chunkProcessor.js'

class UploadWorker {
    constructor() {
        this.chunkProcessor = new ChunkProcessor()
        this.activeControllers = new Map()
        this.isCancelled = false
    }

    // 创建可取消的fetch请求
    createAbortableFetch(url, options, taskId) {
        const controller = new AbortController()
        this.activeControllers.set(taskId, controller)
        
        return {
            controller,
            fetch: fetch(url, {
                ...options,
                signal: controller.signal
            })
        }
    }

    // 处理单个分片上传
    async handleChunkUpload(data, taskId) {
        const { chunkData, uploadConfig } = data
        const { url, headers } = uploadConfig

        if (this.isCancelled) {
            throw new Error('上传已取消')
        }

        const formData = new FormData()
        formData.append('chunk', chunkData.chunk)
        formData.append('index', chunkData.index)
        formData.append('totalChunks', chunkData.totalChunks)
        formData.append('hash', chunkData.hash)
        formData.append('filename', chunkData.file.name)

        try {
            const { controller, fetch: fetchPromise } = this.createAbortableFetch(
                url,
                {
                    method: 'POST',
                    body: formData,
                    headers: {
                        ...headers,
                        'Content-Range': `bytes ${chunkData.start}-${chunkData.end - 1}/${chunkData.file.size}`
                    }
                },
                taskId
            )

            const response = await fetchPromise
            
            this.activeControllers.delete(taskId)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }

            return response.json()
        } catch (error) {
            this.activeControllers.delete(taskId)
            if (error.name === 'AbortError') {
                throw new Error('上传已取消')
            }
            throw error
        }
    }

    // 处理流式上传
    async handleStreamUpload(data) {
        const { file, uploadConfig } = data
        const chunks = []
        
        for await (const chunkData of this.chunkProcessor.generateChunks(file)) {
            if (this.isCancelled) {
                throw new Error('上传已取消')
            }

            const result = await this.handleChunkUpload({
                chunkData,
                uploadConfig
            }, `chunk-${chunkData.index}`)
            
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

    // 取消所有上传
    cancelAll() {
        this.isCancelled = true
        this.activeControllers.forEach(controller => controller.abort())
        this.activeControllers.clear()
        
        // 重置取消状态
        setTimeout(() => {
            this.isCancelled = false
        }, 100)
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
                result = await uploadWorker.handleChunkUpload(data, taskId)
                break
            case 'STREAM_UPLOAD':
                result = await uploadWorker.handleStreamUpload(data)
                break
            case 'CANCEL_UPLOAD':
                uploadWorker.cancelAll()
                self.postMessage({
                    type: 'UPLOAD_CANCELLED',
                    taskId
                })
                return
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