<template>
  <div class="video-panel">
    <div class="video-wrapper">
      <div class="video-frame">
        <img :src="currentFrame" alt=""/>
      </div>
      <div class="video-controls">
        <input
          type="range"
          v-model="currentProgress"
          min="0"
          max="100"
          class="progress-bar"
        />
        <div class="time-display">
          {{ formattedTime }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// 响应式状态
const isPlaying = ref(false)
const currentProgress = ref(0)
const frames = ref({
  list: [],
  total: 1,
  fps: 30
})
let playTimer = null

// 计算属性
const currentFrame = computed(() => {
  const totalFrames = frames.value.total || 1
  const frameIndex = Math.min(
    Math.floor((currentProgress.value / 100) * totalFrames),
    totalFrames - 1
  )
  return frames.value.list[frameIndex] || ''
})

const formattedTime = computed(() => {
  const totalFrames = frames.value.total || 1
  const fps = frames.value.fps || 30
  const totalSeconds = (currentProgress.value / 100) * totalFrames / fps

  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.floor(totalSeconds % 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})

const frameStep = computed(() => {
  return (100 / Math.max(frames.value.total - 1, 1)).toFixed(4)
})

// 方法
const loadFrames = async () => {
  try {
    const response = await fetch('/api/frames')
    const { total, prefix, files, fps } = await response.json()

    // 预加载所有图片
    const preloadImages = urls => {
      urls.forEach(url => {
        const img = new Image()
        img.src = url
      })
    }

    const frameUrls = files.map(f => `${prefix}${f}`)
    preloadImages(frameUrls)

    frames.value = {
      list: frameUrls,
      total: Math.max(total, 1),
      fps: Math.max(fps, 1)
    }

    currentProgress.value = 0
  } catch (error) {
    console.error('帧加载失败:', error)
  }
}

const togglePlay = () => {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) {
    const interval = 1000 / frames.value.fps
    playTimer = setInterval(() => {
      const newProgress = currentProgress.value + (100 / (frames.value.total - 1))
      currentProgress.value = newProgress >= 100 ? 100 : Number(newProgress.toFixed(4))
      if (newProgress >= 100) togglePlay()
    }, interval)
  } else {
    clearInterval(playTimer)
  }
}

const handleSeek = (e) => {
  const step = parseFloat(frameStep.value)
  currentProgress.value = Math.round(e.target.value / step) * step
}

// 生命周期
onMounted(loadFrames)
</script>


<style scoped src="@/assets/css/video.css"></style>
