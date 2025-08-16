<template>
  <div class="chart-container">
    <h2>球轨迹散点图</h2>
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup>
import * as echarts from 'echarts';
import { onMounted, onUnmounted, ref, watch } from 'vue';

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
});

const chartRef = ref(null);
let chartInstance = null;

const initChart = () => {
  if (!chartRef.value || !props.data) return;

  chartInstance = echarts.init(chartRef.value);
  
  const scatterData = props.data.xyFrameSpeedData.map(p => [p[0], p[1], p[2], p[3]]);
  const maxSpeed = Math.max(...props.data.speedData.filter(s => s !== null));

  const option = {
    tooltip: {
      formatter: params => `帧: ${params.value[2]}<br/>坐标: (${params.value[0].toFixed(1)}, ${params.value[1].toFixed(1)})<br/>速度: ${params.value[3].toFixed(2)} 像素/秒`
    },
    xAxis: {
      type: 'value',
      min: props.data.xRange.min - 50,
      max: props.data.xRange.max + 50,
      axisLabel: {
        formatter: value => value.toFixed(0)
      }
    },
    yAxis: {
      type: 'value',
      inverse: true,
      min: props.data.yRange.min - 50,
      max: props.data.yRange.max + 50,
      axisLabel: {
        formatter: value => value.toFixed(0)
      }
    },
    visualMap: {
      min: 0,
      max: maxSpeed,
      dimension: 3,
      right: 10,
      inRange: { color: ['#313695', '#a50026'] }
    },
    series: [
      {
        type: 'scatter',
        symbolSize: 16,
        data: scatterData,
        itemStyle: { borderColor: '#000', borderWidth: 0.5 }
      },
      {
        type: 'line',
        data: props.data.xyConnectedData,
        lineStyle: { opacity: 0.5 },
        showSymbol: false
      }
    ]
  };

  chartInstance.setOption(option);
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

watch(() => props.data, () => {
  initChart();
}, { deep: true });
</script>

<style scoped>
.chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  padding: 15px 0 0 0;
  min-width: 400px;
}

.chart {
  width: 100%;
  height: 400px;
}

h2 {
  margin-left: 15px;
  color: #2c3e50;
  font-size: 16px;
}
</style>