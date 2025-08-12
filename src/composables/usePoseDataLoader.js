import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import frameCache from '@/composables/frameCache'


export function usePoseDataLoader() {
  const auth = useAuthStore()
  const frames = ref([])
  const poseFrames = ref([])
  const poseData = ref(null)
  const loading = ref(false)
  const poseLoading = ref(false)

  // 加载普通帧
  const loadFrames = async (videoId) => {
    loading.value = true
    try {
      // 先尝试从IndexedDB获取缓存
      const cachedFrames = await frameCache.getBatch(videoId, 9999)
      if (cachedFrames && cachedFrames.length > 0) {
        console.log(`从缓存加载 ${cachedFrames.length} 个普通帧`)
        frames.value = cachedFrames
        loading.value = false
        return cachedFrames
      }

      // 缓存未命中，从服务器获取
      const response = await fetch(`/api/frames-batch/${videoId}`, {
        headers: { Authorization: `Bearer ${auth.token}` },
        cache: 'force-cache'  // 强制使用缓存
      })
      const { data } = await response.json()
      const frameData = data?.frames || []

      // 存储到IndexedDB缓存
      if (frameData.length > 0) {
        await frameCache.setBatch(videoId, frameData)
        console.log(`缓存 ${frameData.length} 个普通帧到IndexedDB`)
      }

      frames.value = frameData
      return frameData
    } catch (error) {
      console.error('加载失败:', error)
      frames.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  // 加载姿态帧
  const loadPoseFrames = async (videoId) => {
    loading.value = true
    try {
      const cachedFrames = await frameCache.getBatch(videoId, 9999)
      if (cachedFrames && cachedFrames.length > 0) {
        console.log(`从缓存加载 ${cachedFrames.length} 个姿态帧`)
        poseFrames.value = cachedFrames
        loading.value = false
        return cachedFrames
      }

      const response = await fetch(`/api/pose-frames/${videoId}`, {
        headers: { Authorization: `Bearer ${auth.token}` },
        cache: 'force-cache'  // 强制使用缓存
      })
      const { data } = await response.json()
      const frameData = data?.frames || []

      if (frameData.length > 0) {
        await frameCache.setBatch(videoId, frameData)
        console.log(`缓存 ${frameData.length} 个姿态帧到IndexedDB`)
      }

      poseFrames.value = frameData
      return frameData
    } catch (error) {
      console.error('加载失败:', error)
      poseFrames.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  // 加载姿态数据
  const loadPoseData = async (videoId) => {
    poseLoading.value = true
    try {
      const response = await fetch(`/api/pose-data/${videoId}`, {
        headers: { Authorization: `Bearer ${auth.token}` },
      })
      const res = await response.json()

      // 添加骨骼点名称翻译映射
      const keypointTranslations = {
        'nose': '鼻子',
        'left_eye': '左眼',
        'right_eye': '右眼',
        'left_ear': '左耳',
        'right_ear': '右耳',
        'left_shoulder': '左肩',
        'right_shoulder': '右肩',
        'left_elbow': '左肘',
        'right_elbow': '右肘',
        'left_wrist': '左腕',
        'right_wrist': '右腕',
        'left_hip': '左髋',
        'right_hip': '右髋',
        'left_knee': '左膝',
        'right_knee': '右膝',
        'left_ankle': '左脚踝',
        'right_ankle': '右脚踝',
      };

      // 翻译keypoint_id2name中的名称
      const translatedKeypointId2name = {};
      if (res.data.meta_info?.keypoint_id2name) {
        for (const [id, name] of Object.entries(res.data.meta_info.keypoint_id2name)) {
          translatedKeypointId2name[id] = keypointTranslations[name] || name;
        }
      }

      // 扁平化处理关键数据结构
      const normalizedData = {
        // 元数据
        meta_info: {
          ...res.data.meta_info,
          keypoint_id2name: translatedKeypointId2name,
          skeleton_links: res.data.meta_info?.skeleton_links || [],
          keypoint_colors: Array.isArray(res.data.meta_info?.keypoint_colors)
            ? res.data.meta_info.keypoint_colors
            : []
        },
        // 实例数据
        instance_info: (res.data.instance_info || []).map(frame => ({
          frame_id: Number(frame.frame_id) || 0,
          instances: (frame.instances || []).map(inst => ({
            bbox: Array.isArray(inst.bbox) ? inst.bbox.flat() : [],
            keypoints: ensure2DArray(inst.keypoints),
            keypoint_scores: Array.isArray(inst.keypoint_scores)
              ? inst.keypoint_scores
              : []
          }))
        }))
      };

      poseData.value = normalizedData;
      return normalizedData;
    } catch (err) {
      console.error('骨骼数据加载失败:', err);
      poseData.value = { error: err.message };
      throw err;
    } finally {
      poseLoading.value = false;
    }
  }

    // 清理缓存
  const clearCache = async (videoId = null) => {
    if (videoId) {
      // 清理特定视频的缓存
      const videoFrames = await frameCache.getVideoFrames(videoId)
      console.log(`清理视频 ${videoId} 的 ${videoFrames.length} 个缓存帧`)
    } else {
      // 清理所有缓存
      await frameCache.clear()
      console.log('清理所有缓存')
    }
  }

  // 辅助函数
  function ensure2DArray(arr) {
    if (!Array.isArray(arr)) return [];
    return arr.map(item =>
      Array.isArray(item) ? item.map(Number) : []
    );
  }

  return {
    frames,
    poseFrames,
    poseData,
    loading,
    poseLoading,
    loadFrames,
    loadPoseFrames,
    loadPoseData,
    // 缓存管理方法
    clearCache,
    hasVideoCache: (videoId) => frameCache.hasVideoCache(videoId)
  }
}