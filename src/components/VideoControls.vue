<script setup>
import { defineProps, defineEmits, ref, inject, watch } from 'vue';


const props = defineProps({
  type: String,
  progress: Number,
  currentTime: Number,
  duration: Number,
  isZoomed: Boolean
})

const emits = defineEmits(['toggle-play', 'seek', 'toggle-zoom']);

// 使用 inject 获取视频引用
const videoRefs = inject('videoRefs', null);
const videoRef = ref(null);

// 监听视频引用变化和类型变化
watch([() => videoRefs, () => props.type], () => {
  if (videoRefs && props.type) {
    videoRef.value = videoRefs[`${props.type}Video`]?.value;
  }
}, {
  immediate: true
});

// 格式化时间的方法
const formatTime = (seconds) => {
  const date = new Date(0);
  date.setSeconds(seconds || 0);
  return date.toISOString().slice(11, 19);
};

</script>

<template>
  <div class="video-controls">
    <!-- 播放/暂停按钮 -->
    <button @click="$emit('toggle-play')">
      {{ $parent.$refs[`${type}Video`]?.paused ? '▶' : '⏸' }}
    </button>

    <!-- 进度条 -->
    <input
      type="range"
      class="progress-bar"
      :value="progress"
      @input="$emit('seek', $event.target.value)"
      min="0"
      max="100"
      step="0.1"
    >

    <!-- 时间显示 -->
    <span class="time-display">
      {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
    </span>

    <!-- 缩放按钮 -->
    <button @click="$emit('toggle-zoom')">
      {{ isZoomed ? '✕' : '⛶' }}
    </button>
  </div>
</template>

<style scoped>
.video-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  margin-top: 10px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: #e0e6ed;
  border-radius: 2px;
}

.time-display {
  color: #5a6a85;
  font-size: 14px;
  min-width: 120px;
  text-align: center;
}

button {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e0e6ed;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

button:hover {
  background: #f1f5f9;
}
</style>