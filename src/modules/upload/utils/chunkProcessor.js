export class ChunkProcessor {
    constructor(chunkSize = 5 * 1024 * 1024) {
        this.chunkSize = chunkSize
        this.activeWorkers = new Map()
    }

    // 文件分片
    createChunks(file) {
        const chunks = []
        const totalSize = file.size
        const totalChunks = Math.ceil(totalSize / this.chunkSize)

        for (let i = 0; i < totalChunks; i++) {
            const start = i * this.chunkSize
            const end = Math.min(start + this.chunkSize, totalSize)
            
            const chunkInfo = {
                file,
                start,
                end,
                index: i,
                totalChunks,
                size: end - start,
                chunk: file.slice(start, end)
            }
            chunks.push(chunkInfo)
        }
        return chunks
    }

    // 创建分片的哈希标识（用于断点续传）
    async createChunkHash(chunk) {
        const buffer = await chunk.arrayBuffer()
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
        // 将哈希结果的 ArrayBuffer 转换为 Uint8Array 数组，方便逐字节处理
        const hashArray = Array.from(new Uint8Array(hashBuffer))
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
    }

    // 流式分片生成器（支持边分片边处理）
    async* generateChunks(file) {
        const totalSize = file.size
        const totalChunks = Math.ceil(totalSize / this.chunkSize)
        
        for (let i = 0; i < totalChunks; i++) {
            const start = i * this.chunkSize
            const end = Math.min(start + this.chunkSize, totalSize)
            const chunk = file.slice(start, end)
            
            const chunkData = {
                file,
                start,
                end,
                index: i,
                totalChunks,
                size: end - start,
                chunk,
                hash: await this.createChunkHash(chunk)
            }
            
            yield chunkData
        }
    }

    // 合并分片信息
    mergeChunkResults(results) {
        return {
            totalSize: results.reduce((sum, r) => sum + r.size, 0),
            uploadedChunks: results.length,
            chunks: results
        }
    }
}