import { defineStore } from 'pinia'
import {computed, ref, watch} from 'vue'
import { useAuthStore } from './auth'
import frameCache from '@/composables/frameCache.js'

// 模拟数据生成器
const generateMockData = () => {
  const baseTime = Date.now();
  
  return Array.from({ length: 20 }, (_, i) => {
    const randomDays = Math.floor(Math.random() * 30) - 15; // -15到+15天
    const randomHours = Math.floor(Math.random() * 24);
    const randomMinutes = Math.floor(Math.random() * 60);
    
    const createTime = new Date(baseTime - (randomDays * 24 * 60 * 60 * 1000) - (randomHours * 60 * 60 * 1000) - (randomMinutes * 60 * 1000));
    const expiryDays = 7 + Math.floor(Math.random() * 8); // 7-14天有效期
    const expiryTime = new Date(createTime.getTime() + (expiryDays * 24 * 60 * 60 * 1000));
    
    // 更真实的状态分布
    let status;
    if (i < 3) {
      status = 'expired';
    } else if (i < 15) {
      status = 'completed';
    } else {
      status = 'processing';
    }
    
    return {
      id: i + 1,
      video_id: `video_${String(i + 1).padStart(4, '0')}`,
      time: createTime.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      status: status,
      expiry: expiryTime.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
    };
  });
}

export const useHistoryStore = defineStore('history', () => {
    const auth = useAuthStore()
    const historyItems = ref([])
    const currentAnalysisId = ref(null)
    const isLoading = ref(false)
    const error = ref(null)

    const initialized = ref(false)
    const polling = ref(null)

    const processingItems = computed(() =>
      historyItems.value.filter(item => item.status === 'processing')
    )

    const setCurrentAnalysisId = (id) => {
        currentAnalysisId.value = id
    }

    const fetchHistory = async () => {
        try {
            if (historyItems.value.length === 0 || processingItems.value.length > 0) {
                isLoading.value = true;
            }
            // 开发环境使用模拟数据
            if (import.meta.env.MODE === 'development') {
                await new Promise(resolve => setTimeout(resolve, 500))

                // 首次加载时强制生成模拟数据
                const newData = generateMockData();
                updateHistoryItems(newData);

                // 检查缓存状态
                for (const item of newData) {
                    const hasCache = await frameCache.hasVideoCache(item.video_id, 'normal');
                    item.cacheStatus = hasCache ? 'cached' : 'not_cached';
                }

                // 设置默认最新记录
                if (historyItems.value.length > 0) {
                    // 过滤出非 processing 状态的记录，并按 ID 降序排列
                    const validRecords = [...historyItems.value]
                        .filter(item => item.status !== 'processing')
                        .sort((a, b) => b.id - a.id)

                    // 优先选择最新非 processing 记录，若没有则保持 null
                    currentAnalysisId.value = validRecords[0]?.id || null;
                    initialized.value = true;
                }
                error.value = null
                return
            }

            // 生产环境真实请求
            const response = await fetch('/api/history', {
                headers: {
                    Authorization: `Bearer ${auth.token}`
                }
            })

            if (!response.ok) {
                const { message } = await response.json()
                error.value = message || '获取历史记录失败'
                return
            }

            const { data } = await response.json()
            const itemsWithCache = await Promise.all(
                data.map(async (item) => {
                    const hasCache = await frameCache.hasVideoCache(item.video_id, 'normal');
                    return {
                        ...item,
                        cacheStatus: hasCache ? 'cached' : 'not_cached'
                    };
                })
            );

            // 使用新函数更新数据，避免完全替换
            updateHistoryItems(itemsWithCache);

            // 设置默认最新记录
            if (!initialized.value && historyItems.value.length > 0) {
                const validRecords = [...historyItems.value]
                    .filter(item => item.status === 'completed')
                    .sort((a, b) => b.id - a.id);
                currentAnalysisId.value = validRecords[0]?.id || null;
                initialized.value = true;
            }

            error.value = null
        } catch (err) {
            error.value = err.message || '请求失败，请检查网络连接'
            console.error('获取历史记录失败:', err)
        } finally {
            // 延迟隐藏加载状态，避免快速闪烁
            setTimeout(() => {
                isLoading.value = false;
            }, 300);
        }
    }

    // 更新历史记录
    const updateHistoryItems = (newItems) => {
        // 如果是首次加载，直接替换
        if (historyItems.value.length === 0) {
            historyItems.value = newItems;
            return;
        }

        const existingItemsMap = new Map(historyItems.value.map(item => [item.id, item]));

        newItems.forEach(newItem => {
            const existingItem = existingItemsMap.get(newItem.id);
            if (existingItem) {
                // 只在状态发生变化时更新
                if (existingItem.status !== newItem.status) {
                    Object.assign(existingItem, newItem);
                }
            } else {
                historyItems.value.push(newItem);
            }
        });

        // 按ID降序排序
        historyItems.value.sort((a, b) => b.id - a.id);
    };

    const deleteItem = async (id) => {
        try {
            const targetId = Number(id)

            // 开发环境模拟删除
            if (import.meta.env.MODE === 'development') {
                historyItems.value = historyItems.value.filter(
                    item => item.id !== targetId
                )

                // 如果删除的是当前选中项，清空选中状态
                if (currentAnalysisId.value === targetId) {
                    currentAnalysisId.value = null
                }

                error.value = null
                return
            }

            // 生产环境请求修改点
            const response = await fetch(`/api/history/${targetId}`, {
                method: 'DELETE',
                headers: {
                    Authorization: `Bearer ${auth.token}`
                }
            })

            if (!response.ok) {
                let errorMessage = '删除项目失败'
                try {
                    // 尝试解析 JSON 错误信息
                    const errorData = await response.json()
                    errorMessage = errorData.message || errorMessage
                } catch (e) {
                    // 当响应不是 JSON 时使用状态文本
                    errorMessage = `${response.status} ${response.statusText}`
                }
                error.value = errorMessage
                return
            }

            historyItems.value = historyItems.value.filter(
                item => item.id !== targetId
            )

            // 清除相关缓存
            await frameCache.clearVideoCache(targetId);

            // 如果删除的是当前选中项，清空选中状态
            if (currentAnalysisId.value === targetId) {
                currentAnalysisId.value = null
            }

            error.value = null
        } catch (err) {
            error.value = err.message || '删除请求失败，请检查网络连接'
            console.error('删除操作失败:', err)
        }
    }

    const cacheItem = async (id) => {
        try {
            const item = historyItems.value.find(item => item.id === id);
            if (!item) return;

            // 设置检查状态
            item.cacheStatus = 'checking';

            if (import.meta.env.MODE === 'development') {
                await new Promise(resolve => setTimeout(resolve, 1000));
                item.cacheStatus = 'cached';
            } else {
                // 生产环境：从服务器获取数据并缓存
                const response = await fetch(`/api/analysis/${id}/data`, {
                    headers: {
                        Authorization: `Bearer ${auth.token}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    // 缓存数据到IndexedDB
                    await frameCache.setBatch(id, data.frames || []);
                    item.cacheStatus = 'cached';
                } else {
                    item.cacheStatus = 'not_cached';
                }
            }
        } catch (error) {
            console.error('缓存数据失败:', error);
            const item = historyItems.value.find(item => item.id === id);
            if (item) item.cacheStatus = 'not_cached';
        }
    };

    // 清除指定项目的缓存
    const clearCacheForItem = async (id) => {
        try {
            const item = historyItems.value.find(item => item.id === id);
            if (!item) return;

            item.cacheStatus = 'checking';
            await frameCache.clearVideoCache(id);
            item.cacheStatus = 'not_cached';
        } catch (error) {
            console.error('清除缓存失败:', error);
        }
    };

    // 自动刷新历史记录
    const startAutoRefresh = () => {
        if (polling.value) {
            clearTimeout(polling.value);
            polling.value = null;
        }
        polling.value = setTimeout(fetchHistory, 30000);
    }

    return {
        historyItems,
        currentAnalysisId,
        isLoading,
        error,
        setCurrentAnalysisId,
        fetchHistory,
        deleteItem,
        cacheItem,
        clearCacheForItem,
        polling,
        startAutoRefresh,
        processingItems
    }
})