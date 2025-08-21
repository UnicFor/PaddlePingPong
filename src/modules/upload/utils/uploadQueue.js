// 完全修复后的UploadQueue.js
export class UploadQueue {
    constructor(maxConcurrency = 4) {
        this.maxConcurrency = maxConcurrency
        this.queue = []
        this.activeUploads = new Set()
        this.completedUploads = new Map()
        this.failedUploads = new Map()
        this.totalTasks = 0
        this.onProgress = null
        this.onComplete = null
        this.onError = null
        this.isCancelled = false
        this.abortControllers = new Map() // 使用AbortController
    }

    // 添加任务到队列
    addTask(chunkData, uploadFn) {
        if (this.isCancelled) return;

        const task = {
            id: `${chunkData.file.name}-${chunkData.index}`,
            chunkData,
            uploadFn,
            retryCount: 0,
            maxRetries: 4,
            abortController: new AbortController() // 每个任务有自己的中断控制器
        }

        this.queue.push(task)
        this.processQueue()
    }

    async processQueue() {
        while (this.activeUploads.size < this.maxConcurrency && this.queue.length > 0) {
            const task = this.queue.shift()
            this.activeUploads.add(task.id)
            this.executeTask(task)
        }
    }

    async executeTask(task) {
        if (this.isCancelled) {
            this.activeUploads.delete(task.id)
            this.abortControllers.delete(task.id)
            return
        }

        try {
            const result = await task.uploadFn(task.chunkData, task.abortController.signal)
            if (this.isCancelled) return

            this.completedUploads.set(task.id, {
                ...result,
                chunkIndex: task.chunkData.index
            })

            this.activeUploads.delete(task.id)
            this.abortControllers.delete(task.id)

            const completed = this.completedUploads.size
            const total = this.totalTasks
            const progress = (completed / total) * 100

            if (this.onProgress && !this.isCancelled) {
                this.onProgress({
                    completed,
                    total,
                    progress: Number(progress.toFixed(2)),
                    chunkInfo: task.chunkData
                })
            }

            if (!this.isCancelled) {
                this.processQueue()
                if (this.isComplete() && !this.isCancelled) {
                    this.onComplete?.(Array.from(this.completedUploads.values()))
                }
            }
        } catch(error) {
            if (error.name === 'AbortError' || this.isCancelled) {
                this.activeUploads.delete(task.id)
                this.abortControllers.delete(task.id)
                return
            }

            task.retryCount++
            if(task.retryCount <= task.maxRetries && !this.isCancelled) {
                const delay = Math.min(1000 * Math.pow(2, task.retryCount - 1), 10000)
                setTimeout(() => {
                    if (!this.isCancelled) {
                        this.queue.unshift(task)
                        this.activeUploads.delete(task.id)
                        this.processQueue()
                    }
                }, delay)
            } else if (!this.isCancelled) {
                this.failedUploads.set(task.id, { task, error })
                this.activeUploads.delete(task.id)
                this.abortControllers.delete(task.id)
                this.onError?.(error, task)
                this.processQueue()
            }
        }
    }

    isComplete() {
        return this.queue.length === 0 && this.activeUploads.size === 0
    }

    cancelAll() {
        this.isCancelled = true
        this.queue = []
        
        this.abortControllers.forEach(controller => {
            controller.abort()
        })
        this.abortControllers.clear()
        
        this.activeUploads.clear()
        this.totalTasks = 0
        
        setTimeout(() => {
            this.isCancelled = false
        }, 100)
    }

    reset() {
        this.queue = []
        this.activeUploads.clear()
        this.completedUploads.clear()
        this.failedUploads.clear()
        this.totalTasks = 0
        this.abortControllers.clear()
    }
}