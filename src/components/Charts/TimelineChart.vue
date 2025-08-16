<script setup>
import * as echarts from 'echarts';
import { onMounted, onUnmounted, ref, watch } from 'vue';

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  frameDataList: {
    type: Array,
    default: () => []
  },
  currentFrameIndex: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['update:currentFrameIndex']);

const chartRef = ref(null);
let chartInstance = null;
const currentFrame = ref('');

const frameStyle = ref({});

const initChart = () => {
  if (!chartRef.value || !props.data) return;

  chartInstance = echarts.init(chartRef.value);
  
  const options = props.data.frameData.map((frame, index) => ({
    title: { text: `球轨迹回放 - 第${frame}帧`, left: 'center' },
    series: [
      {
        name: '历史轨迹',
        type: 'scatter',
        data: props.data.xyFrameSpeedData.filter(p => p[2] <= frame),
        symbolSize: 10,
        itemStyle: { color: '#91cc75', opacity: 0.5 }
      },
      {
        name: '当前位置',
        type: 'effectScatter',
        data: [getSafeData(index)],
        symbolSize: 20,
        rippleEffect: { brushType: 'stroke' },
        itemStyle: { color: '#f4e925' }
      }
    ]
  }));

  const option = {
    baseOption: {
      timeline: {
        axisType: 'category',
        autoPlay: true,
        playInterval: 500,
        data: props.data.frameData,
        label: { formatter: value => `帧${value}` }
      },
      grid: { left: '5%', right: '5%', bottom: '25%' },
      xAxis: {
        type: 'value',
        min: props.data.xRange.min - 50,
        max: props.data.xRange.max + 50,
      },
      yAxis: {
        type: 'value',
        inverse: true,
        min: props.data.yRange.min - 50,
        max: props.data.yRange.max + 50,
      },
    },
    options: options
  };

  chartInstance.setOption(option);

  chartInstance.on('timelinechanged', params => {
    try {
      if (!props.frameDataList || props.frameDataList.length === 0) {
        currentFrame.value = '';
        return;
      }

      const maxAllowedIndex = Math.max(props.frameDataList.length - 1, 0);
      const safeIndex = Math.min(params.currentIndex, maxAllowedIndex);
      const finalIndex = Math.max(safeIndex, 0);

      currentFrame.value = props.frameDataList[finalIndex] || '';
      frameStyle.value = currentFrame.value 
        ? { backgroundImage: `url(${currentFrame.value})` }
        : {};
      
      emit('update:currentFrameIndex', finalIndex);
    } catch (e) {
      console.error('帧更新错误:', e);
    }
  });
};

const getSafeData = (index) => {
  return props.data.xyFrameSpeedData[index] || [0, 0, 0, 0];
};

const handleResize = () => {
  chartInstance?.resize({ animation: { duration: 300 } });
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
});

watch([() => props.data, () => props.frameDataList], () => {
  initChart();
}, { deep: true });
</script>

<template>
  <div class="chart-container full-width">
    <h2>时间轴轨迹回放</h2>
    <div ref="chartRef" class="chart">
      <div class="frame-background" :style="frameStyle"></div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  padding: 15px 0 0 0;
  min-width: 400px;
  position: relative;
}

.chart-container.full-width {
  grid-column: 1 / -1;
}

.chart {
  width: 100%;
  height: 400px;
  position: relative;
}

.frame-background {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  opacity: 0.3;
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  pointer-events: none;
}

h2 {
  margin-left: 15px;
  color: #2c3e50;
  font-size: 16px;
}
</style>