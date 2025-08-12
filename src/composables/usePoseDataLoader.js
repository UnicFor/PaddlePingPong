import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

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
      const response = await fetch(`/api/frames-batch/${videoId}`, {
        headers: { Authorization: `Bearer ${auth.token}` }
      })
      const { data } = await response.json()
      frames.value = data?.frames || []
      return frames.value
    } catch (error) {
      console.error('加载失败:', error)
      return []
    } finally {
      loading.value = false
    }
  }

  // 加载姿态帧
  const loadPoseFrames = async (videoId) => {
    loading.value = true
    try {
      const response = await fetch(`/api/pose-frames/${videoId}`, {
        headers: { Authorization: `Bearer ${auth.token}` }
      })
      const { data } = await response.json()
      poseFrames.value = data?.frames || []
      return poseFrames.value
    } catch (error) {
      console.error('加载失败:', error)
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
        headers: { Authorization: `Bearer ${auth.token}` }
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
    loadPoseData
  }
}