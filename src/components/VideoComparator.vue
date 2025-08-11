<script setup>
import { defineProps, ref, onMounted, onBeforeUnmount, reactive, provide } from 'vue';
// 导入子组件
import VideoControls from "./VideoControls.vue";

const props = defineProps({
  originalSrc: String,
  processedSrc: String
});

// 定义视频播放器参数
const state = reactive({
  isSyncing: false,
  progress: { original: 0, processed: 0 },
  currentTime: { original: 0, processed: 0 },
  duration: { original: 0, processed: 0 },
  isZoomed: { original: false, processed: false }
});

// 定义视频引用
const originalVideo = ref(null);
const processedVideo = ref(null);
const originalPanel = ref(null);
const processedPanel = ref(null);

// 使用 provide 提供视频引用
provide('videoRefs', {
  originalVideo,
  processedVideo
});


// 挂载时执行
onMounted(() => {
  // 添加全屏变化事件监听
  document.addEventListener('fullscreenchange', handleFullscreenChange);
});

// 卸载前执行
onBeforeUnmount(() => {
  // 移除全屏变化事件监听
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
});

// 切换播放/暂停
const togglePlay = (type) => {
  const video = type === 'original' ? originalVideo.value : processedVideo.value;
  video.paused ? video.play() : video.pause();
};

// 处理暂停事件
const handlePause = () => {
  if (state.isSyncing) {
    originalVideo.value.pause();
    processedVideo.value.pause();
  }
};

// 更新进度
const updateProgress = (event, type) => {
  const video = event.target;
  state.currentTime[type] = video.currentTime;
  state.duration[type] = video.duration;
  state.progress[type] = (video.currentTime / video.duration) * 100 || 0;

  if (state.isSyncing && type === "original") {
    processedVideo.value.currentTime = video.currentTime;
  }
};

// 处理跳转
const handleSeek = (value, type) => {
  const video = type === 'original' ? originalVideo.value : processedVideo.value;
  video.currentTime = (value * video.duration) / 100;
};

// 切换同步状态
const toggleSync = () => {
  state.isSyncing = !state.isSyncing;
  if (state.isSyncing) {
    syncVideos();
  }
};

// 同步播放视频
const syncVideos = async () => {
  await Promise.all([
    originalVideo.value.play(),
    processedVideo.value.play()
  ]);
};

// 处理播放事件
const handlePlay = () => {
  if (state.isSyncing) syncVideos();
};

// 切换缩放
const toggleZoom = async (type) => {
  const panel = type === 'original' ? originalPanel.value : processedPanel.value;
  if (!state.isZoomed[type]) {
    await enterFullscreen(panel);
    state.isZoomed[type] = true;
  } else {
    await exitFullscreen();
    state.isZoomed[type] = false;
  }
};

// 进入全屏
const enterFullscreen = async (element) => {
  if (element.requestFullscreen) {
    return element.requestFullscreen();
  } else if (element.webkitRequestFullscreen) { /* Safari */
    return element.webkitRequestFullscreen();
  } else if (element.msRequestFullscreen) { /* IE11 */
    return element.msRequestFullscreen();
  }
  console.warn('Fullscreen API is not supported');
};

// 退出全屏
const exitFullscreen = async () => {
  if (document.exitFullscreen) {
    await document.exitFullscreen();
  } else if (document.webkitExitFullscreen) { /* Safari */
    await document.webkitExitFullscreen();
  } else if (document.msExitFullscreen) { /* IE11 */
    await document.msExitFullscreen();
  }
};

// 处理全屏变化
const handleFullscreenChange = () => {
  if (!document.fullscreenElement) {
    state.isZoomed.original = false;
    state.isZoomed.processed = false;
  }
};
</script>

<template>
  <div class="video-comparator">
    <div class="global-controls">
      <h2>视频分析（原视频 / 处理视频）</h2>
      <button class="sync-button" @click="toggleSync">
        {{ isSyncing ? '断开同步' : '同步播放' }}
      </button>
    </div>
    <div class="comparison-container">
      <!-- 原始视频 -->
      <div
        class="video-panel"
        :class="{ 'fullscreen-mode': isZoomed?.original }"
        ref="originalPanel"
      >
        <div class="video-wrapper">
          <div class="video-frame">
            <video
              ref="originalVideo"
              :src="originalSrc"
              @play="handlePlay('original')"
              @pause="handlePause('original')"
              @timeupdate="(e) => updateProgress(e, 'original')"
            ></video>
          </div>
          <video-controls
            type="original"
            :progress="progress?.original || 0"
            :current-time="currentTime?.original || 0"
            :duration="duration?.original || 0"
            :is-zoomed="isZoomed?.original || false"
            @toggle-play="togglePlay('original')"
            @seek="(value) => handleSeek(value, 'original')"
            @toggle-zoom="() => toggleZoom('original')"
          />
        </div>
      </div>

      <!-- 处理后视频 -->
      <div
        class="video-panel"
        :class="{ 'fullscreen-mode': isZoomed?.processed }"
        ref="processedPanel"
      >
        <div class="video-wrapper">
          <div class="video-frame">
            <video
              ref="processedVideo"
              :src="processedSrc"
              @play="handlePlay('processed')"
              @pause="handlePause('processed')"
              @timeupdate="(e) => updateProgress(e, 'processed')"
            ></video>
          </div>
          <video-controls
            type="processed"
            :progress="progress?.processed || 0"
            :current-time="currentTime?.processed || 0"
            :duration="duration?.processed || 0"
            :is-zoomed="isZoomed?.processed || false"
            @toggle-play="togglePlay('processed')"
            @seek="(value) => handleSeek(value, 'processed')"
            @toggle-zoom="() => toggleZoom('processed')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-comparator {
  padding: 1rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(32, 62, 92, 0.12);
  margin-bottom: 2rem;
  overflow: hidden;
}

/* 比较容器 - 使用grid布局 */
.comparison-container {
  display: grid;
  gap: 1rem; /* 增加间距提升可读性 */
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
}

/* 视频面板 */
.video-panel {
  background: white;
  border-radius: 12px;
  margin: 0.6rem 0.4rem;
}

.video-panel.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: #000;
  border-radius: 0;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

/* 视频框架 - 全屏模式优化 */
.fullscreen-mode .video-frame {
  height: calc(100% - 60px);
  width: 100%;
  margin: 0;
  border-radius: 0;
}

/* 视频框架 */
.video-frame {
  position: relative;
  aspect-ratio: 16/9; /* 保持视频比例 */
  border-radius: 8px;
  overflow: hidden;
  background: #000;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1); /* 内边框效果 */
}

/* 全屏模式下的视频框架 */
.fullscreen-mode .video-frame {
  height: calc(100vh - 100px); /* 调整高度计算 */
  width: calc(100vw - 2rem);
  margin: 1rem auto;
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.global-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.4rem;
}

.global-controls h2{
  margin: 0 0 0 0.6rem;
  font-size: 1.6rem;
  font-weight: 600;
}

/* 同步按钮 */
.sync-button {
  background: #2c3e50;
  color: white;
  border: none;
  padding: 0.6rem 1.6rem;
  border-radius: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sync-button:hover {
  background: #34495e;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(44, 62, 80, 0.25);
}

.sync-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(44, 62, 80, 0.2);
}

@media (max-width: 768px) {
  .comparison-container {
    grid-template-columns: 1fr;
  }

  .video-wrapper {
    margin: 0.75rem;
  }

  .fullscreen-mode .video-frame {
    height: calc(100vh - 80px);
    margin: 0.75rem auto;
  }

  .global-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0 0.75rem;
  }

  .global-controls h2 {
    font-size: 1.2rem;
  }

  .sync-button {
    width: 100%;
    justify-content: center;
  }
}
</style>