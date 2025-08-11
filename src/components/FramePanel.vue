<template>
  <div class="video-panel">
    <div class="video-wrapper">
      <div class="frame-panel">
        <h2>视频帧分析</h2>
        <!-- 视频帧容器 -->
        <div class="video-frame" style="position: relative">
          <img
            :src="currentFrame"
            alt=""
            @load="handleImageLoad"
          />
          <div ref="skeletonOverlay" class="skeleton-overlay" style="position: absolute"></div>
          <div v-if="loading" class="loading-overlay">
            <div class="loading-text">加载中... {{ loadedCount }}/{{ totalFrames }}</div>
          </div>
        </div>

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
              <input type="checkbox" v-model="showLabels"> 显示关键点标签
            </label>
            <label>
              <input type="checkbox" v-model="showDebug"> 显示调试信息
            </label>
          </div>
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
        <AnalysisTabs
          :video-id="videoId"
        />
      </div>

      <!-- 调试面板 -->

      <div v-if="showDebug" class="debug-panel-title">
        <h2 >调试面板</h2>
        <div v-if="showDebug" class="debug-panel">
        <div class="instance-container">
          <div v-for="(instance, index) in debugInstances" :key="index" class="instance-card">
            <div class="instance-header">
              <h3>实例 {{ index + 1 }}</h3>
              <div class="confidence-badge" :style="getConfidenceStyle(instance.avgConfidence)">
                {{ (instance.avgConfidence * 100).toFixed(0) }}%
              </div>
            </div>

            <!-- 边界框信息 -->
            <div class="bbox-info">
              <span class="data-label">边界框:</span>
              <span class="data-value">({{ instance.bbox.x1 }}, {{ instance.bbox.y1 }}) → ({{ instance.bbox.x2 }}, {{ instance.bbox.y2 }})</span>
            </div>

            <!-- 关键点表格 -->
            <table class="keypoint-table">
              <thead>
                <tr>
                  <th>关键点</th>
                  <th>X坐标</th>
                  <th>Y坐标</th>
                  <th>置信度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(kpt, kidx) in instance.keypoints" :key="kidx">
                  <td>{{ kpt.name }}</td>
                  <td>{{ kpt.x }}</td>
                  <td>{{ kpt.y }}</td>
                  <td>
                    <span class="confidence-bar" :style="getConfidenceBarStyle(kpt.score)">
                      {{ (kpt.score * 100).toFixed(0) }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AnalysisTabs from "@/components/AnalysisTabs.vue";
const auth = useAuthStore()

const props = defineProps({
  videoId: {
    type: String,
    required: true
  }
})

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
const debugInstances = computed(() => {
  if (!poseData.value?.instance_info?.length) return []

  const frameData = poseData.value.instance_info.find(
    f => f.frame_id === currentFrameIndex.value
  )

  return (frameData?.instances || []).map(instance => {
    const keypoints = (instance.keypoints || []).map((kpt, kidx) => ({
      name: poseData.value.meta_info?.keypoint_id2name?.[kidx] || `点${kidx}`,
      x: kpt[0]?.toFixed(1) || 'NaN',
      y: kpt[1]?.toFixed(1) || 'NaN',
      score: instance.keypoint_scores?.[kidx] || 0
    }))

    const bbox = instance.bbox || []
    const scores = keypoints.map(k => k.score)
    const avgConfidence = scores.length > 0
      ? scores.reduce((a, b) => a + b, 0) / scores.length
      : 0

    return {
      bbox: {
        x1: bbox[0]?.toFixed(1) || 'NaN',
        y1: bbox[1]?.toFixed(1) || 'NaN',
        x2: bbox[2]?.toFixed(1) || 'NaN',
        y2: bbox[3]?.toFixed(1) || 'NaN'
      },
      keypoints,
      avgConfidence
    }
  })
})

// 样式计算函数
const getConfidenceStyle = (score) => ({
  backgroundColor: `hsl(${score * 120}, 70%, 40%)`,
  color: score > 0.6 ? 'white' : '#333'
})

const getConfidenceBarStyle = (score) => ({
  width: `${score * 100}%`,
  backgroundColor: `hsl(${score * 120}, 70%, 50%)`
})

// 图像加载处理
const handleImageLoad = () => {

  if (!showCoordinates.value || !poseData.value?.instance_info) return

  nextTick(async () => {
    const img = await waitForImageLoad()
    const overlay = skeletonOverlay.value
    overlay.innerHTML = ''

    if (!img || !overlay) return

    try {
      const rect = img.getBoundingClientRect()
      const { naturalWidth, naturalHeight } = img
      const scaleX = rect.width / naturalWidth
      const scaleY = rect.height / naturalHeight

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
              display: showBBox.value ? 'block' : 'none',
              position: 'absolute',
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
              display: showSkeleton.value ? 'block' : 'none',
              position: 'absolute',
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

const waitForImageLoad = () => {
  return new Promise(resolve => {
    const img = document.querySelector('.video-frame img')
    if (img.complete) return resolve(img)
    img.onload = () => resolve(img)
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
});

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

        const res = await response.json();

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

<style scoped src="@/assets/css/frame.css"></style>