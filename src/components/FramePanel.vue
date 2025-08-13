<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { usePoseDataLoader } from '@/composables/usePoseDataLoader'

const props = defineProps({
  videoId: {
    type: String,
    required: true
  }
})

// 使用 composable 函数
const {
  frames, 
  poseFrames, 
  poseData, 
  loading, 
  poseLoading, 
  loadFrames, 
  loadPoseFrames, 
  loadPoseData, 
} = usePoseDataLoader()


// 状态管理
const currentFrames = ref([])
const loadedCount = ref(0)
const currentProgress = ref(0)
const skeletonOverlay = ref(null)

// 显示选项
const showPanel = ref(true)
const showPose = ref(false)
const showCoordinates = ref(false)
const showSkeleton = ref(false)
const showBBox = ref(false)
const showDebug = ref(false)
const currentInstanceIndex = ref(0)

// 计算属性
const totalFrames = computed(() => currentFrames.value.length)
const currentFrameIndex = computed(() => currentProgress.value + 1)
const currentFrame = computed(() => currentFrames.value[currentProgress.value] || '')

// 调试信息
const debugInstances = computed(() => {
  if (!poseData.value?.instance_info?.length) return []

  // 找到当前帧的数据
  const frameData = poseData.value.instance_info.find(
    f => f.frame_id === currentFrameIndex.value
  )

  return (frameData?.instances || []).map(instance => {

    // 处理每个关键点信息
    const keypoints = (instance.keypoints || []).map((kpt, kidx) => ({
      name: poseData.value.meta_info?.keypoint_id2name?.[kidx] || `点${kidx}`,
      x: kpt[0]?.toFixed(1) || 'NaN',
      y: kpt[1]?.toFixed(1) || 'NaN',
      score: instance.keypoint_scores?.[kidx] || 0
    }))

    // 处理边界框信息
    const bbox = instance.bbox || []
    // 计算平均置信度
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
// 置信度样式
const getConfidenceStyle = (score) => ({
  backgroundColor: `hsl(${score * 120}, 70%, 40%)`,
  color: score > 0.6 ? 'white' : '#333'
})
// 置信度进度条样式
const getConfidenceBarStyle = (score) => ({
  width: `${score * 100}%`,
  backgroundColor: `hsl(${score * 120}, 70%, 50%)`
})

// 导航控制
const prevFrame = () => currentProgress.value > 0 && currentProgress.value--
const nextFrame = () => currentProgress.value < totalFrames.value - 1 && currentProgress.value++

// 图像加载处理
const handleImageLoad = () => {
  if (!showCoordinates.value || !poseData.value?.instance_info) return

  nextTick(async () => {
    const img = await waitForImageLoad()
    const overlay = skeletonOverlay.value
    overlay.innerHTML = ''

    if (!img || !overlay) return

    drawSkeletonAndBBox(img, overlay)
  })
}

// 重绘函数
const redraw = async () => {
  const overlay = skeletonOverlay.value
  if (!overlay) return

  // 清除现有绘制内容
  overlay.innerHTML = ''

  // 如果不显示坐标，直接返回
  if (!showCoordinates.value || !poseData.value?.instance_info) return

  const img = await waitForImageLoad()
  if (!img) return

  drawSkeletonAndBBox(img, overlay)
}

// 主要绘图函数
const drawSkeletonAndBBox = (img, overlay) => {
  try {
    const rect = img.getBoundingClientRect()
    const { naturalWidth, naturalHeight } = img
    const scaleX = rect.width / naturalWidth
    const scaleY = rect.height / naturalHeight

    const frameData = poseData.value.instance_info?.find(f =>
        f.frame_id === currentFrameIndex.value
    )

    if (!frameData?.instances) return

    frameData.instances.forEach((instance, index) => {
      // 绘制边界框
      if (showBBox.value && Array.isArray(instance.bbox)) {
        drawBBox(overlay, instance.bbox, scaleX, scaleY, index)
      }

      // 绘制骨骼点
      if (showSkeleton.value && Array.isArray(instance.keypoints)) {
        drawKeypoints(overlay, instance.keypoints, scaleX, scaleY)
      }
    })
  } catch (e) {
    console.error('渲染错误:', e)
  }
}

// 绘制边界框函数
const drawBBox = (overlay, bbox, scaleX, scaleY, instanceIndex) => {
  if (bbox.length < 4) return
  
  const [x1, y1, x2, y2] = bbox
  const width = (x2 - x1) * scaleX
  const height = (y2 - y1) * scaleY
  const left = x1 * scaleX
  const top = y1 * scaleY

  // 创建边框容器
  const bboxContainer = document.createElement('div')
  Object.assign(bboxContainer.style, {
    position: 'absolute',
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`,
    pointerEvents: 'none',
    zIndex: '1001'
  })

  // 创建边框
  const bboxEl = document.createElement('div')
  Object.assign(bboxEl.style, {
    position: 'absolute',
    width: '100%',
    height: '100%',
    border: '2px solid #3b82f6',
    borderRadius: '8px',
    boxSizing: 'border-box'
  })

  // 创建标签
  const labelEl = document.createElement('div')
  Object.assign(labelEl.style, {
    position: 'absolute',
    top: '-24px',
    right: '8px',
    background: '#3b82f6',
    color: 'white',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 'bold',
    whiteSpace: 'nowrap',
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
    zIndex: '1002'
  })
  labelEl.textContent = `实例${instanceIndex + 1}`

  // 组装元素
  bboxContainer.appendChild(bboxEl)
  bboxContainer.appendChild(labelEl)
  overlay.appendChild(bboxContainer)
}

// 绘制关键点函数
const drawKeypoints = (overlay, keypoints, scaleX, scaleY) => {
  keypoints.forEach((kpt) => {
    if (kpt.length < 2) return

    const [x, y] = kpt
    // 绘制点
    const pointEl = document.createElement('div')
    Object.assign(pointEl.style, {
      left: `${x * scaleX}px`,
      top: `${y * scaleY}px`,
      display: 'block',
      position: 'absolute',
      width: '6px',
      height: '6px',
      background: 'red',
      borderRadius: '50%',
      transform: 'translate(-50%, -50%)',
    })
    overlay.appendChild(pointEl)
  })
}

const waitForImageLoad = () => {
  return new Promise(resolve => {
    const img = document.querySelector('.video-frame img')
    if (img.complete) return resolve(img)
    img.onload = () => resolve(img)
  })
}

// 监听显示选项变化
watch(showPose, async (newVal) => {
  if (newVal && poseFrames.value.length === 0) {
    await loadPoseFrames(props.videoId)
  }
  if (newVal) {
    currentFrames.value = poseFrames.value
  } else {
    currentFrames.value = frames.value
  }
  currentFrames.value = newVal ? poseFrames.value : frames.value
})

watch([frames, poseFrames], () => {
  // 当帧数据更新时，重新计算当前显示
  if (showPose.value) {
    currentFrames.value = poseFrames.value
  } else {
    currentFrames.value = frames.value
  }
})

watch(showCoordinates, (newVal) => {
  if (newVal && !poseData.value) loadPoseData(props.videoId)
  // 无论开启还是关闭坐标绘制，都触发重绘
  redraw()
});

// 监听骨骼点和边界框显示选项变化
watch([showSkeleton, showBBox], () => {
  redraw()
})

// 面板显示状态变化会影响布局，需要重绘
watch(showPanel, () => {
  redraw()
})

// 监听当前帧变化
watch(currentProgress, () => {
  redraw()
})

// 监听布局变化
onMounted(() => {
  window.addEventListener('resize', redraw)
})

onUnmounted(() => {
  window.removeEventListener('resize', redraw)
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
    await loadFrames(newVal)
    currentFrames.value = frames.value
  }
})

// 调试面板显示控制关联
watch(showDebug, (newVal) => {
  if (newVal && !showPanel.value) {
    showPanel.value = true;
  }
});

watch(showPanel, (newVal) => {
  if (!newVal && showDebug.value) {
    showDebug.value = false;
  }
});
</script>

<template>
  <div class="video-panel">
    <div class="frame-panel">
        <h2>视频帧分析</h2>
        <!-- 视频帧容器 -->
        <div class="video-frame" style="position: relative">
          <img
            :src="currentFrame"
            alt=""
            @load="handleImageLoad"
          />
          <!-- TODO:使用Canvas替代div overlay -->
          <div ref="skeletonOverlay" class="skeleton-overlay" style="position: absolute"></div>
          <div v-if="loading" class="loading-overlay">
            <div class="loading-text">加载中... {{ loadedCount }}/{{ totalFrames }}</div>
          </div>
        </div>

        <!-- 选项面板 -->
        <div class="options-panel">
          <div style="display: flex; flex-direction: row; justify-content: space-between; gap: 1rem;">
            <div style="display: flex; flex-direction: row; gap: 1rem;">
              <label>
                <input type="checkbox" v-model="showPanel"> 显示右侧面板
              </label>
                <label>
                <input type="checkbox" v-model="showPose"> 添加骨骼点检测
              </label>
              <label>
                <input type="checkbox" v-model="showCoordinates"> 添加坐标绘制
                <span v-if="poseLoading">(加载中...)</span>
              </label>
            </div>

            <!-- TODO 缓存状态显示 
            <div class="cache-status">
              <span v-if="cacheStatus.isLoading" style="color: #666;">检查缓存中...</span>
              <span v-else-if="cacheStatus.isCached" style="color: green;">📦 图片帧文件已缓存</span>
              <span v-else style="color: #8B4513;">📦 文件未缓存</span>
              <button 
                v-if="cacheStatus.isCached" 
                @click="handleClearCache(props.videoId)" 
                class="cache-button"
              >
                清理本视频缓存
              </button>
            </div>
            -->

          </div>

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
    </div>

    <div v-if="showPanel" class="debug-panel">
      <h2 >调试面板</h2>
      <div v-if="showDebug" class="debug-content">
        <div class="instance-container">
          <!-- 当前选中的实例信息 -->
          <div v-if="debugInstances.length > 0" class="instance-card">
            <div class="instance-header">
              <div v-if="debugInstances.length > 1" class="instance-switcher">
                <label>选择实例:</label>
                <select v-model="currentInstanceIndex">
                  <option v-for="(instance, index) in debugInstances" :key="index" :value="index">
                    实例 {{ index + 1 }}
                  </option>
                </select>
              </div>
              <div class="confidence-badge" :style="getConfidenceStyle(debugInstances[currentInstanceIndex].avgConfidence)">
                骨骼平均置信度: {{ (debugInstances[currentInstanceIndex].avgConfidence * 100).toFixed(0) }}%
              </div>
            </div>

              <!-- 边界框信息 -->
            <div class="bbox-info">
              <span class="data-label">边界框:</span>
              <span class="data-value">({{ debugInstances[currentInstanceIndex].bbox.x1 }}, {{ debugInstances[currentInstanceIndex].bbox.y1 }}) → ({{ debugInstances[currentInstanceIndex].bbox.x2 }}, {{ debugInstances[currentInstanceIndex].bbox.y2 }})</span>
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
                <tr v-for="(kpt, kidx) in debugInstances[currentInstanceIndex].keypoints" :key="kidx">
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
      <div v-else class="debug-content">
        <div class="usage-guide">
          <h3>视频帧分析使用说明</h3>
          
          <div class="guide-section">
            <h4>⚙️ 左侧选项控制</h4>
            <ul>
              <li><strong>显示骨骼点检测</strong> - 在视频帧上绘制人体关键点标记</li>
              <li><strong>添加坐标绘制</strong> - 在每个骨骼点旁显示具体坐标值</li>
              <li><strong>显示骨骼点</strong> - 显示/隐藏所有检测到的骨骼点</li>
              <li><strong>显示边界框</strong> - 显示/隐藏人物检测边界框</li>
              <li><strong>显示调试信息</strong> - 在右侧面板显示详细调试数据</li>
            </ul>
          </div>

          <div class="guide-section">
            <h4>📋 右侧面板功能</h4>
            <p>右侧面板显示当前视频中每帧的详细分析数据，包括检测到的骨骼点坐标、置信度和边界框信息。</p>
          </div>

          <div class="guide-tips">
            <h4>💡 使用提示</h4>
            <p>使用底部进度条可快速浏览不同帧的分析结果。勾选相应选项即可实时查看对应的可视化效果。</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-panel {
  position: relative;
  display: flex;
  padding: 1rem;
  gap: 1rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(32, 62, 92, 0.12);
  transition: transform 0.3s cubic-bezier(0.23, 1, 0.32, 1);
  margin-bottom: 0.8rem;
}

.frame-panel {
  flex: 1 0 600px;
  max-width: none;
  margin: 0;
}

.debug-panel {
  flex: 1;
  background: #ffffff;
  min-width: 420px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow-y: auto;
}

.debug-panel h2 {
  margin: 1rem 1rem 0 1rem;
  color: #1e293b;
  font-size: 1.6rem;
  font-weight: 600;
}

.options-panel {
  display: flex;
  flex-direction: column;
  min-width: 390px;
  margin: 1rem 0;
  padding: 1.2rem;
  background: #e8edf3;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.options-panel label {
  align-items: center;
  display: flex;
  cursor: pointer;
  font-size: 14px;
  color: #334155;
  transition: all 0.2s ease;
}

.options-panel input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  accent-color: #3b82f6;
  border-radius: 4px;
}

.cache-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 14px;
  font-weight: 600;
  color: green;
}

.cache-button {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.cache-button:hover {
  background: #5190f6;
}

.skeleton-controls {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.skeleton-overlay {
  position: absolute !important;
  top: 0;
  left: 0;
  z-index: 1000;
  transform: translateZ(0);
  width: 100%;
  height: 100%;
  pointer-events: none;
  background-color: transparent;
}

.navigation-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 1.2em;
  color: #333;
}

.video-frame {
  position: relative;
  aspect-ratio: 16/9;
  margin-bottom: 20px;
  transition: filter 0.3s ease;
}

.video-frame img {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  z-index: 1;
}

.loading-status {
  padding: 10px;
  background: #f0f0f0;
  margin-top: 10px;
  text-align: center;
}

.video-controls {
  display: flex;
  margin: 10px auto 10px;
  padding: 12px 24px;
  background: #f8fafc;
  gap: 16px;
  border-radius: 16px;
}

.progress-bar {
  flex: 1;
  height: 5px;
  background: #e0e6ed;
  border-radius: 3px;
  width: 100%;
  max-width: 1600px;
  margin-top: 8px;
  margin-right: 8px;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

.progress-bar::-webkit-slider-thumb:hover {
  width: 8px;
  height: 18px;
}

.progress-bar::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  background: #2c3e50;
  border-radius: 50%;
  cursor: grab;
  transition: all 0.2s;
}

.progress-bar::-webkit-slider-thumb:active {
  cursor: grabbing;
  transform: scale(1.2);
}

.time-display {
  color: #5a6a85;
  font-size: 14px;
  letter-spacing: 1px;
  max-width: 60px;
  display: flex;
  justify-content: space-between;
  min-width: 80px;
  align-items: center;
}

.time-display::before {
  opacity: 0.7;
}

input[type="range"] {
  width: 100%;
  margin: 15px 0;
}

.sync-button {
  background: #2c3e50;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
}

.sync-button:hover {
  background: #34495e;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(44, 62, 80, 0.2);
}

/* 调试面板 */
.instance-container {
  display: grid;
  gap: 1rem;
}

.instance-switcher {
  padding: 0.5rem;
  background: #f0f0f0;
  border-radius: 4px;
}

.instance-switcher label {
  margin-right: 0.5rem;
  font-weight: 500;
}

.instance-switcher select {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  background: white;
}

.instance-card {
  background: white;
  padding: 1rem;
}

.instance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.keypoint-table tr:hover td {
  background-color: #f8f9fa;
}

.confidence-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: bold;
}

.data-label {
  font-weight: 500;
  color: #2c3e50;
  margin-right: 0.5rem;
}

.data-value {
  color: #666;
}

.keypoint-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.keypoint-table th {
  background: #f4f6f8;
  padding: 0.6rem;
  text-align: left;
  font-size: 0.9em;
}

.keypoint-table td {
  padding: 0.6rem;
  border-bottom: 1px solid #eee;
}

.confidence-bar {
  display: inline-block;
  height: 24px;
  min-width: 40px;
  padding: 0 8px;
  color: white;
  text-align: center;
  border-radius: 4px;
  line-height: 24px;
  font-size: 0.85em;
}

.usage-guide {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 1rem 2rem;
  color: #334155;
  line-height: 1.6;
}

.usage-guide h3 {
  margin: 0 0 1rem 0;
  color: #1e293b;
  font-size: 1.2rem;
  font-weight: 600;
}

.guide-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid #3b82f6;
}

.guide-section h4 {
  margin: 0 0 0.75rem 0;
  color: #1e293b;
  font-size: 1rem;
  font-weight: 500;
}

.guide-section p {
  margin: 0;
  font-size: 0.875rem;
  color: #475569;
}

.guide-section ul {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.guide-section li {
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: #475569;
}

.guide-tips {
  margin-top: 2rem;
  padding: 1rem;
  background: #fef3c7;
  border-radius: 8px;
  border-left: 3px solid #f59e0b;
}

.guide-tips h4 {
  margin: 0 0 0.5rem 0;
  color: #92400e;
  font-size: 1rem;
  font-weight: 500;
}

.guide-tips p {
  margin: 0;
  font-size: 0.875rem;
  color: #78350f;
}

@media (max-width: 1500px) {
  .video-panel {
    border-radius: 6px;
    display: flex;
    flex-direction: column;
  }
  .video-wrapper {
    margin: 10px;
  }
  .video-frame {
    margin-bottom: 4px;
    border-radius: 6px;
    transition: filter 0.3s ease;
  }
}
</style>