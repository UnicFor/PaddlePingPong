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
    // 设计原理：该函数的主要目的是为文件分片生成唯一的哈希标识，用于断点续传场景。
    // 在断点续传中，通过比较分片的哈希值可以判断该分片是否已经成功上传，避免重复上传相同内容。
    // 
    // 理论知识：
    // 1. arrayBuffer()：Blob 对象（chunk 本质是一个 Blob）的方法，用于将其内容转换为 ArrayBuffer。
    //    ArrayBuffer 是一个表示二进制数据的通用缓冲区，在 JavaScript 中用于处理二进制数据。
    // 2. crypto.subtle.digest()：Web Crypto API 提供的方法，用于计算数据的哈希值。
    //    这里使用的是 SHA-256 算法，它是一种安全哈希算法，能够将任意长度的数据转换为固定长度（256 位）的哈希值。
    //    SHA-256 具有以下特性：
    //    - 确定性：相同的输入总是产生相同的输出。
    //    - 唯一性：不同的输入几乎不可能产生相同的输出（哈希碰撞概率极低）。
    //    - 不可逆性：无法从哈希值反向推导出原始数据。
    // 3. Uint8Array：用于以 8 位无符号整数的形式查看 ArrayBuffer 中的数据。
    // 4. 十六进制转换：将每个字节转换为两位的十六进制字符串，方便阅读和存储。
    async createChunkHash(chunk) {
        const buffer = await chunk.arrayBuffer()
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
        // 将哈希结果的 ArrayBuffer 转换为 Uint8Array 数组，方便逐字节处理
        const hashArray = Array.from(new Uint8Array(hashBuffer))
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
    }

    // 流式分片生成器（支持边分片边处理）
    // 核心设计理念：使用异步生成器函数（async*）实现流式分片。异步生成器允许函数在执行过程中暂停并返回一个值，
    // 之后可以恢复执行。在文件分片场景下，每次生成一个分片后立即返回，而不需要等待所有分片都处理完成，
    // 从而实现边分片边处理的流式操作，减少内存占用并提高处理效率。
    // 
    // 理论知识：
    // 1. 异步生成器函数（async*）：结合了异步函数（async）和生成器函数（*）的特性。
    //    生成器函数可以使用 yield 关键字暂停执行并返回值。因此，异步生成器函数可以在异步操作中逐个生成值。
    // 2. 流式处理：流式处理是一种数据处理模式，数据不是一次性加载到内存中，而是分块处理。这样可以减少内存占用，
    //    尤其适用于处理大文件，避免一次性加载整个文件导致内存不足。
    // 3. Blob.slice()：Blob 对象的方法，用于从现有 Blob 中提取一个新的 Blob 对象。该方法是轻量级的，
    //    不会立即读取文件内容，只有在需要时才会访问文件数据，符合流式处理的思想。
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