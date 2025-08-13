// 帧缓存管理类
/*
1. 普通帧缓存：按视频ID和帧类型（normal）存储
2. 姿态帧缓存：按视频ID和帧类型（pose）存储
3. 缓存过期：默认7天过期，可配置

TODO
1. 配置LRU缓存策略
2. 配额管理
*/

class FrameCacheManager {
  constructor() {
    this.dbName = 'PaddleFrameCacheDB'
    this.version = 2
    this.storeName = 'frames'
    this.db = null
    this.maxAge = 7 * 24 * 60 * 60 * 1000 // 7天过期
  }

  // 初始化数据库
  async init() {
    if (this.db) return this.db

    return new Promise((resolve, reject) => {
      // 创建IndexedDB数据库连接
      const request = indexedDB.open(this.dbName, this.version)
      
      // 错误处理
      request.onerror = () => {
        console.error('IndexedDB初始化失败:', request.error)
        reject(request.error)
      }

      // 成功处理
      request.onsuccess = () => {
        this.db = request.result
        resolve(this.db)
      }

      // 数据库升级
      request.onupgradeneeded = (e) => {
        const db = e.target.result
        if (e.oldVersion < 2) {
          // 删除旧存储空间并重新创建
          if (db.objectStoreNames.contains(this.storeName)) {
            db.deleteObjectStore(this.storeName)
          }
          
          const store = db.createObjectStore(this.storeName, { keyPath: 'id' })
          store.createIndex('timestamp', 'timestamp', { unique: false })
          store.createIndex('videoId', 'videoId', { unique: false })
          store.createIndex('frameType', 'frameType', { unique: false })  // 帧类型索引
          store.createIndex('videoId_frameType', ['videoId', 'frameType'], { unique: false })  // 复合索引
        }
      }
    })
  }

  // 存储帧数据
  async set(id, data, frameType = 'normal', metadata = {}) {
    try {
        const db = await this.init()
        const tx = db.transaction(this.storeName, 'readwrite')
        const store = tx.objectStore(this.storeName)

        const record = {
            id,
            data,
            timestamp: Date.now(),
            size: JSON.stringify(data).length,
            frameType,
            ...metadata
        }

        return store.put(record)
    } catch (error) {
        console.error('设置缓存失败:', error)
        throw error
    }
  }

  // 获取帧数据
  async get(id, frameType = null) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      
      const result = await store.get(id)
      
      // 检查帧类型匹配和过期
      if (result && 
          (frameType === null || result.frameType === frameType) && 
          (Date.now() - result.timestamp) < this.maxAge) {
        return result.data
      }
      
      // 过期删除
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
  async setBatch(videoId, frames, frameType = 'normal') {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readwrite')
      const store = tx.objectStore(this.storeName)
      
      // 清理该视频指定类型的旧缓存
      await this.clearVideoCache(videoId, frameType, store)
      
      // 存储新数据
      const promises = frames.map((frameData, index) => {
        const id = `${videoId}_${frameType}_frame_${index}`
        return store.put({
          id,
          data: frameData,
          videoId,
          frameType,  // 新增帧类型
          frameIndex: index,
          timestamp: Date.now()
        })
      })
      
      await Promise.all(promises)
      return true
    } catch (error) {
      console.error('批量存储失败:', error)
      throw error
    }
  }

  // 批量获取帧数据
  async getBatch(videoId, frameType = 'normal') {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      const index = store.index('videoId_frameType')
      
      return new Promise((resolve, reject) => {
        const request = index.getAll([videoId, frameType])
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
      console.error('批量获取失败:', error)
      return []
    }
  }

  // 检查某个视频指定类型是否有缓存
  async hasVideoCache(videoId, frameType = null) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      
      if (frameType) {
        const index = store.index('videoId_frameType')
        return new Promise((resolve, reject) => {
          const request = index.openCursor(IDBKeyRange.only([videoId, frameType]))
          request.onsuccess = () => resolve(!!request.result)
          request.onerror = () => reject(request.error)
        })
      } else {
        const index = store.index('videoId')
        return new Promise((resolve, reject) => {
          const request = index.openCursor(IDBKeyRange.only(videoId))
          request.onsuccess = () => resolve(!!request.result)
          request.onerror = () => reject(request.error)
        })
      }
    } catch (error) {
      console.error('检查视频缓存失败:', error)
      return false
    }
  }

  // 获取某个视频指定类型的所有缓存
  async getVideoFrames(videoId, frameType = null) {
    try {
      const db = await this.init()
      const tx = db.transaction(this.storeName, 'readonly')
      const store = tx.objectStore(this.storeName)
      
      if (frameType) {
        const index = store.index('videoId_frameType')
        return new Promise((resolve, reject) => {
          const request = index.getAll([videoId, frameType])
          request.onsuccess = () => {
            const results = request.result
              .filter(r => (Date.now() - r.timestamp) < this.maxAge)
              .sort((a, b) => a.frameIndex - b.frameIndex)
              .map(r => r.data)
            resolve(results)
          }
          request.onerror = () => reject(request.error)
        })
      } else {
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
      }
    } catch (error) {
      console.error('获取视频帧失败:', error)
      return []
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

  // 清理过期数据
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

    // 清理特定视频的缓存
  async clearVideoCache(videoId, frameType = null, store = null) {
    try {
      const db = store ? null : await this.init()
      const tx = store ? null : db.transaction(this.storeName, 'readwrite')
      const actualStore = store || tx.objectStore(this.storeName)
      
      if (frameType) {
        // 清理指定类型的缓存
        const index = actualStore.index('videoId_frameType')
        return new Promise((resolve, reject) => {
          const request = index.openCursor(IDBKeyRange.only([videoId, frameType]))
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
      } else {
        // 清理该视频所有缓存
        const index = actualStore.index('videoId')
        return new Promise((resolve, reject) => {
          const request = index.openCursor(IDBKeyRange.only(videoId))
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
      }
    } catch (error) {
      console.error('清理视频缓存失败:', error)
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