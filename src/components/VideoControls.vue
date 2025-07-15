<!-- VideoControls.vue -->
<!-- VideoControls.vue -->
<template>
  <div class="video-controls">
    <button @click="$emit('toggle-play')">
      {{ $parent.$refs[`${type}Video`]?.paused ? '▶' : '⏸' }}
    </button>

    <input
      type="range"
      class="progress-bar"
      :value="progress"
      @input="$emit('seek', $event.target.value)"
      min="0"
      max="100"
      step="0.1"
    >

    <span class="time-display">
      {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
    </span>

    <button @click="$emit('toggle-zoom')">
      {{ isZoomed ? '✕' : '⛶' }}
    </button>
  </div>
</template>

<script>
export default {
  props: {
    type: String,
    progress: Number,
    currentTime: Number,
    duration: Number,
    isZoomed: Boolean
  },
  methods: {
    formatTime(seconds) {
      const date = new Date(0)
      date.setSeconds(seconds || 0)
      return date.toISOString().slice(11, 19)
    }
  }
}
</script>

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