<template>
  <div class="video-panel">
    <div class="video-wrapper">
      <h2>视频帧分析</h2>

      <!-- 选项面板 -->
      <div class="options-panel">
        <label>
          <input type="checkbox" v-model="showPose"> 添加骨骼点检测
        </label>
        <label>
          <input type="checkbox" v-model="showCoordinates"> 添加坐标绘制
          <span v-if="poseLoading">(加载中...)</span>
        </label>

        <div v-if="showCoordinates" class="skeleton-controls">
          <label>
            <input type="checkbox" v-model="showSkeleton"> 显示骨骼点
          </label>
          <label>
            <input type="checkbox" v-model="showBBox"> 显示边界框
          </label>
          <label>
            <input type="checkbox" v-model="showDebug"> 显示调试信息
          </label>
          <label>
            <input type="checkbox" v-model="showLabels"> 显示关键点标签
          </label>
        </div>
      </div>

      <!-- 视频帧容器 -->
      <div class="video-frame">
        <img
          :src="currentFrame"
          alt=""
          @load="handleImageLoad"
        />
        <div ref="skeletonOverlay" class="skeleton-overlay"></div>
        <div v-if="loading" class="loading-overlay">
          <div class="loading-text">加载中... {{ loadedCount }}/{{ totalFrames }}</div>
        </div>
      </div>

      <!-- 调试面板 -->
      <div v-if="showDebug" class="debug-panel">
        <pre>{{ debugInfo }}</pre>
      </div>

      <!-- 视频控制 -->
      <div class="video-controls">
        <input
          type="range"
          v-model.number="currentProgress"
          :min="0"
          :max="totalFrames - 1"
          step="1"
          :disabled="loading"
        />
        <div class="time-display">
          {{ currentFrameIndex }} / {{ totalFrames }}
        </div>
      </div>

      <!-- 导航按钮 -->
      <div class="navigation-buttons">
        <button
            @click="prevFrame"
            :disabled="currentProgress === 0"
            class="sync-button"
        >上一帧</button>
        <button
            @click="nextFrame"
            :disabled="currentProgress === totalFrames - 1"
            class="sync-button"
        >下一帧</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  videoId: {
    type: String,
    required: true
  }
})

const auth = useAuthStore()

// 状态管理
const frames = ref([])
const poseFrames = ref([])
const currentFrames = ref([])
const loading = ref(true)
const loadedCount = ref(0)
const currentProgress = ref(0)
const skeletonOverlay = ref(null)
const poseLoading = ref(false)

// 显示选项
const showPose = ref(false)
const showCoordinates = ref(false)
const showSkeleton = ref(true)
const showBBox = ref(false)
const showDebug = ref(false)
const showLabels = ref(false)
let poseData = ref(null)

// 计算属性
const totalFrames = computed(() => currentFrames.value.length)
const currentFrameIndex = computed(() => currentProgress.value + 1)
const currentFrame = computed(() => currentFrames.value[currentProgress.value] || '')

// 调试信息
const debugInfo = computed(() => {
  // 三级数据校验
  if (!poseData.value?.instance_info?.length) {
    return '骨骼数据加载中或格式异常'
  }

  const frameData = poseData.value.instance_info.find(f =>
    f.frame_id === currentFrameIndex.value
  )

  // 校验找到的帧数据
  if (!frameData?.instances?.length) {
    return `帧 ${currentFrameIndex.value} 无检测实例`
  }

  let info = `=== 帧 ${currentFrameIndex.value} ===\n`
  frameData.instances.forEach((inst, idx) => {
    info += `实例 ${idx + 1}:\n`

    if (Array.isArray(inst.bbox) && inst.bbox.length >= 4) {
      const [x1, y1, x2, y2] = inst.bbox
      info += `边界框: x1=${x1.toFixed(1)}, y1=${y1.toFixed(1)}, x2=${x2.toFixed(1)}, y2=${y2.toFixed(1)}\n`
    }

    if (Array.isArray(inst.keypoints)) {
      const keyPointNames = poseData.value.meta_info?.keypoint_id2name || {}
      info += "关键点:\n"
      inst.keypoints.forEach((kpt, kidx) => {
        const name = keyPointNames[kidx] || `点${kidx}`
        const score = inst.keypoint_scores?.[kidx]?.toFixed(2) ?? 'N/A'
        info += `  ${name}: [${kpt[0]?.toFixed(1) ?? 'NaN'}, ${kpt[1]?.toFixed(1) ?? 'NaN'}], 置信度: ${score}\n`
      })
    }
    info += '\n'
  })
  return info
})

// 图像加载处理
const handleImageLoad = () => {
  if (!showCoordinates.value || !poseData.value?.instance_info) return

  nextTick(() => {
    const img = document.querySelector('.video-frame img')
    const overlay = skeletonOverlay.value
    overlay.innerHTML = ''

    if (!img || !overlay) return

    try {
      const scaleX = img.clientWidth / img.naturalWidth
      const scaleY = img.clientHeight / img.naturalHeight

      const frameData = poseData.value.instance_info?.find(f =>
        f.frame_id === currentFrameIndex.value
      )

      if (!frameData?.instances) return

      const keyPointNames = poseData.value.meta_info?.keypoint_id2name || {}

      frameData.instances.forEach(instance => {
        // 绘制边界框
        if (showBBox.value && Array.isArray(instance.bbox)) {
          if (instance.bbox.length >= 4) {
            const [x1, y1, x2, y2] = instance.bbox
            const bbox = document.createElement('div')
            bbox.className = 'bbox'
            Object.assign(bbox.style, {
              left: `${x1 * scaleX}px`,
              top: `${y1 * scaleY}px`,
              width: `${(x2 - x1) * scaleX}px`,
              height: `${(y2 - y1) * scaleY}px`,
              display: showBBox.value ? 'block' : 'none'
            })
            overlay.appendChild(bbox)
          }
        }

        // 绘制骨骼点
        if (showSkeleton.value && Array.isArray(instance.keypoints)) {
          instance.keypoints.forEach((kpt, kidx) => {
            if (kpt.length < 2) return

            const [x, y] = kpt
            const pointEl = document.createElement('div')
            pointEl.className = 'keypoint'
            Object.assign(pointEl.style, {
              left: `${x * scaleX}px`,
              top: `${y * scaleY}px`,
              display: showSkeleton.value ? 'block' : 'none'
            })
            overlay.appendChild(pointEl)

            // 绘制标签
            if (showLabels.value) {
              const label = document.createElement('div')
              label.className = 'keypoint-label'
              label.textContent = keyPointNames[kidx] || `点${kidx}`
              Object.assign(label.style, {
                left: `${x * scaleX}px`,
                top: `${y * scaleY}px`,
                transform: 'translate(-50%, -100%)'
              })
              overlay.appendChild(label)
            }
          })
        }
      })
    } catch (e) {
      console.error('渲染错误:', e)
    }
  })
}

// 导航控制
const prevFrame = () => currentProgress.value > 0 && currentProgress.value--
const nextFrame = () => currentProgress.value < totalFrames.value - 1 && currentProgress.value++

// 监听显示选项变化
watch(showPose, async (newVal) => {
  if (newVal && poseFrames.value.length === 0) {
    poseFrames.value = await loadFrames(props.videoId, true)
  }
  currentFrames.value = newVal ? poseFrames.value : frames.value
})

watch(showCoordinates, (newVal) => {
  if (newVal && !poseData.value) loadPoseData(props.videoId)
})

// 初始化
onMounted(async () => {
  if (props.videoId) {
    frames.value = await loadFrames(props.videoId)
    currentFrames.value = frames.value
    loading.value = false
  }
})

watch(() => props.videoId, async (newVal) => {
  if (newVal) {
    frames.value = await loadFrames(newVal)
    currentFrames.value = frames.value
    poseFrames.value = []
    poseData.value = null
  }
})

// 帧加载逻辑
const loadFrames = async (videoId, isPose = false) => {
  const endpoint = isPose ? `/api/pose-frames/${videoId}` : `/api/frames-batch/${videoId}`
  try {
    const response = await fetch(endpoint, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    const { data } = await response.json()
    return data?.frames || []
  } catch (error) {
    console.error('加载失败:', error)
    return []
  }
}

async function loadPoseData(videoId) {
    try {
        const response = await fetch(`/api/pose-data/${videoId}`, {
            headers: { Authorization: `Bearer ${auth.token}` }
        });

        if (!response.ok) throw new Error(`HTTP错误 ${response.status}`);

        const res = await response.json();
        if (!res.success) throw new Error(res.message || '未知错误');

        // 扁平化处理关键数据结构
        const normalizedData = {
            meta_info: {
                ...res.data.meta_info,
                skeleton_links: res.data.meta_info?.skeleton_links || [],
                keypoint_colors: Array.isArray(res.data.meta_info?.keypoint_colors)
                    ? res.data.meta_info.keypoint_colors
                    : []
            },
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
    }
}

// 新增辅助函数
function ensure2DArray(arr) {
    if (!Array.isArray(arr)) return [];
    return arr.map(item =>
        Array.isArray(item) ? item.map(Number) : []
    );
}
</script>

<style src="@/assets/css/frame.css"></style>