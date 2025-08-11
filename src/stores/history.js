import { defineStore } from 'pinia'
import {computed, ref, watch} from 'vue'
import { useAuthStore } from './auth'

// 模拟数据生成器
const generateMockData = () => {
  const baseTime = Date.now();
  return Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    time: new Date(baseTime + i * 1000).toLocaleString(),
    status: i === 0 ? 'expired' : (i === 9 ? 'processing' : 'completed'),
    expiry: "2024-03-20"
  }));
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
            historyItems.value = data.map(item => ({
              id: item.id,
              user_id: item.user_id,
              video_id: item.video_id,
              time: item.time,
              status: item.status,
              expiry: item.expiry
            }))

            // 使用新函数更新数据，避免完全替换
            updateHistoryItems(data);

            // 设置默认最新记录 (保持不变)
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

    // 添加新函数用于智能更新历史记录
    const updateHistoryItems = (newItems) => {
        // 如果是首次加载，直接替换
        if (historyItems.value.length === 0) {
            historyItems.value = newItems;
            return;
        }

        // 创建现有ID的映射
        const existingItemsMap = new Map(historyItems.value.map(item => [item.id, item]));

        // 更新或添加项目
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
            const response = await fetch(`/api/history/${targetId}`, {  // 修改1：URL添加路径参数
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
        polling,
        startAutoRefresh,
        processingItems
    }
})