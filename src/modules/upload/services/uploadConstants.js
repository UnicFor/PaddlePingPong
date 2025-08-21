// src/modules/upload/services/uploadConstants.js

// 开发者模式配置
export const DEV_MODE_CONFIG = {
    CHUNK_SIZE: 5 * 1024 * 1024,  // 5MB
    MAX_CONCURRENCY: 2,
    SIMULATE_FAILURE_RATE: 0.02,   // 2% 模拟失败率
    SIMULATE_DELAY_MIN: 200,       // 最小延迟 200ms
    SIMULATE_DELAY_MAX: 800,       // 最大延迟 800ms
    MERGE_DELAY: 2000              // 合并延迟 2s
}

// 生产模式配置
export const PROD_MODE_CONFIG = {
    CHUNK_SIZE: 5 * 1024 * 1024,   // 5MB
    MAX_CONCURRENCY: 4,
    TIMEOUT: 10000                 // 10秒超时
}

// 状态消息
export const STATUS_MESSAGES = {
    SUCCESS: '文件已经上传完毕，请耐心等待系统进行处理',
    CANCELLED: '上传已取消',
    ERROR_PREFIX: '上传失败: '
}

// API 端点
export const API_ENDPOINTS = {
    CHUNK_UPLOAD: '/api/upload/chunk',
    CHUNK_MERGE: '/api/upload/merge',
    UPLOAD_STATUS: '/api/upload/status'
}