export class WorkerManager {
    constructor(workerInstance) {
        this.worker = workerInstance
        this.tasks = new Map()
        this.taskId = 0
    }

    async uploadChunk(chunkData, uploadConfig) {
        return new Promise((resolve, reject) => {
            const taskId = ++this.taskId
            
            this.tasks.set(taskId, { resolve, reject })
            
            this.worker.postMessage({
                type: 'UPLOAD_CHUNK',
                taskId,
                chunkData,
                uploadConfig
            })
        })
    }

    // 处理 Worker 消息
    setupMessageHandler() {
        this.worker.onmessage = (event) => {
            const { type, taskId, result, error } = event.data
            
            if (type === 'CHUNK_UPLOADED') {
                const task = this.tasks.get(taskId)
                if (task) {
                    task.resolve(result)
                    this.tasks.delete(taskId)
                }
            } else if (type === 'CHUNK_ERROR') {
                const task = this.tasks.get(taskId)
                if (task) {
                    task.reject(error)
                    this.tasks.delete(taskId)
                }
            }
        }
    }

    // 终止所有任务
    terminate() {
        this.worker.terminate()
        this.tasks.clear()
    }
}