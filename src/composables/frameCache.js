class FrameCacheManager {
  constructor() {
    this.dbName = 'PaddleFrameCacheDB'
    this.version = 1
    this.storeName = 'frames'
    this.db = null
    this.maxAge = 7 * 24 * 60 * 60 * 1000 // 7天过期
  }

  // 初始化数据库
  async init() {
    if (this.db) return this.db

    return new Promise((resolve, reject) => {
        const request = indexedDB.open(this.dbName, this.version)

        request.onerror = () => {
            console.error('IndexedDB初始化失败:', request.error)
            reject(request.error)
        }

        request.onsuccess = () => {
            this.db = request.result
            resolve(this.db)
        }

        // 数据库升级
        request.onupgradeneeded = (e) => {
            const db = e.target.result
            if (!db.objectStoreNames.contains(this.storeName)) {
                const store = db.createObjectStore(this.storeName, { keyPath: 'id' })
                store.createIndex('timestamp', 'timestamp', { unique: false })
                store.createIndex('videoId', 'videoId', { unique: false })
            }
        }
    })
  }

  async set(id, data, metadata = {}) {
    try {
        const db = await this.init()
        const tx = db.transaction(this.storeName, 'readwrite')
        const store = tx.objectStore(this.storeName)

        const record = {
            id,
            data,
            timestamp: Date.now(),
            size: JSON.stringify(data).length,
            ...metadata
        }

        return store.put(record)
    } catch (error) {
        console.error('设置缓存失败:', error)
        throw error
    }
  }

  // 获取帧数据
  async get(id) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      
      const result = await store.get(id)
      
      // 检查是否过期
      if (result && (Date.now() - result.timestamp) < this.maxAge) {
        return result.data
      }
      
      // 过期则删除
      if (result) {
        this.delete(id)
      }
      
      return null
    } catch (error) {
      console.error('获取数据失败:', error)
      return null
    }
  }

  // 删除单个数据
  async delete(id) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readwrite')
      const store = tx.objectStore(this.storeName)
      
      return store.delete(id)
    } catch (error) {
      console.error('删除数据失败:', error)
    }
  }

  // 批量存储帧数据
  async setBatch(videoId, frames) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readwrite')
      const store = tx.objectStore(this.storeName)
      
      const promises = frames.map((frameData, index) => {
        const id = `${videoId}_frame_${index}`
        return store.put({
          id,
          data: frameData,
          videoId,
          frameIndex: index,
          timestamp: Date.now()
        })
      })
      
      return Promise.all(promises)
    } catch (error) {
      console.error('批量存储失败:', error)
      throw error
    }
  }

  // 批量获取帧数据
  async getBatch(videoId, count) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      
      const frames = []
      for (let i = 0; i < count; i++) {
        const id = `${videoId}_frame_${i}`
        const result = await store.get(id)
        if (result && (Date.now() - result.timestamp) < this.maxAge) {
          frames.push(result.data)
        } else if (result) {
          // 过期数据删除
          this.delete(id)
        }
      }
      
      return frames.length === count ? frames : null
    } catch (error) {
      console.error('批量获取失败:', error)
      return null
    }
  }

  async cleanup() {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readwrite')
      const store = tx.objectStore(this.storeName)
      const index = store.index('timestamp')
      
      const cutoffTime = Date.now() - this.maxAge
      const range = IDBKeyRange.upperBound(cutoffTime)
      
      return new Promise((resolve, reject) => {
        const request = index.openCursor(range)
        request.onsuccess = () => {
          const cursor = request.result
          if (cursor) {
            cursor.delete()
            cursor.continue()
          } else {
            resolve()
          }
        }
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('清理过期数据失败:', error)
    }
  }

  async getStats() {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      
      return new Promise((resolve, reject) => {
        const request = store.count()
        request.onsuccess = () => {
          resolve({
            count: request.result,
            maxAge: this.maxAge
          })
        }
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('获取统计失败:', error)
      return { count: 0, maxAge: this.maxAge }
    }
  }

  // 清空所有缓存
  async clear() {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readwrite')
      const store = tx.objectStore(this.storeName)
      
      return store.clear()
    } catch (error) {
      console.error('清空缓存失败:', error)
    }
  }

  // 检查某个视频是否有缓存
    async hasVideoCache(videoId) {
    try {
        const db = await this.init()
        const tx = db.transaction(this.storeName, 'readonly')
        const store = tx.objectStore(this.storeName)
        const index = store.index('videoId')
        
        return new Promise((resolve, reject) => {
            const request = index.openCursor(IDBKeyRange.only(videoId))
            request.onsuccess = () => {
            const cursor = request.result
            resolve(!!cursor) // 只要找到第一条记录就返回true
            }
            request.onerror = () => reject(request.error)
        })
    } catch (error) {
        console.error('检查视频缓存失败:', error)
        return false
    }
    }

  // 获取某个视频的所有缓存
  async getVideoFrames(videoId) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      const index = store.index('videoId')
      
      return new Promise((resolve, reject) => {
        const request = index.getAll(videoId)
        request.onsuccess = () => {
          const results = request.result
            .filter(r => (Date.now() - r.timestamp) < this.maxAge)
            .sort((a, b) => a.frameIndex - b.frameIndex)
            .map(r => r.data)
          
          resolve(results)
        }
        request.onerror = () => reject(request.error)
      })
    } catch (error) {
      console.error('获取视频帧失败:', error)
      return []
    }
  }
}

const frameCache = new FrameCacheManager()
// 导出使用方法

// 自动清理过期数据（每天一次）
setInterval(() => {
  frameCache.cleanup()
}, 24 * 60 * 60 * 1000)

export default frameCache