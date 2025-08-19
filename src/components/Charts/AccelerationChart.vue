<script setup>
import * as echarts from 'echarts';
import { onMounted, onUnmounted, ref, watch, computed } from 'vue';
import { debounce } from '@/utils/debounce.js';

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
});

const chartRef = ref(null);
let chartInstance = null;

// 数据清洗函数
const cleanData = (points, speeds) => {
  if (!points || points.length === 0) return { cleanPoints: [], xRange: 0, yRange: 0, filteredCount: 0 };
  
  // 计算X和Y的总极差
  const xValues = points.map(p => p[0]).filter(x => x !== null && !isNaN(x));
  const yValues = points.map(p => p[1]).filter(y => y !== null && !isNaN(y));
  
  if (xValues.length === 0 || yValues.length === 0) {
    return { cleanPoints: [], xRange: 0, yRange: 0, filteredCount: 0 };
  }
  
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  
  const xRange = xMax - xMin;
  const yRange = yMax - yMin;
  
  // 过滤异常数据
  const thresholdX = xRange * 0.4; // 40%的极差
  const thresholdY = yRange * 0.4; // 40%的极差
  
  const cleanPoints = [];
  let filteredCount = 0;
  
  for (let i = 1; i < points.length; i++) {
    const prev = points[i-1];
    const curr = points[i];
    
    if (!prev || !curr || !Array.isArray(prev) || !Array.isArray(curr)) continue;
    
    const dx = Math.abs(curr[0] - prev[0]);
    const dy = Math.abs(curr[1] - prev[1]);
    
    // 检查是否为异常数据
    if (dx <= thresholdX && dy <= thresholdY) {
      cleanPoints.push({
        x: curr[0],
        y: curr[1],
        frame: curr[2],
        speed: speeds[i] || 0,
        index: i
      });
    } else {
      filteredCount++;
    }
  }
  
  return { 
    cleanPoints, 
    xRange, 
    yRange, 
    filteredCount
  };
};

// 计算击球事件数据（基于X方向变向，使用清洗后的数据）
const hitEvents = computed(() => {
  if (!props.data?.xyFrameSpeedData || !props.data?.speedData) return [];
  
  const points = props.data.xyFrameSpeedData;
  const speeds = props.data.speedData;
  
  if (!Array.isArray(points) || !Array.isArray(speeds) || points.length === 0) return [];
  
  // 数据清洗
  const { cleanPoints } = cleanData(points, speeds);
  
  if (cleanPoints.length < 3) return [];
  
  const hitEvents = [];
  const frameInterval = 1/30; // 30fps
  
  // 寻找X方向变向点
  for (let i = 1; i < cleanPoints.length - 1; i++) {
    const prev = cleanPoints[i-1];
    const curr = cleanPoints[i];
    const next = cleanPoints[i+1];
    
    if (!prev || !curr || !next) continue;
    
    // 计算X方向变化
    const currDirX = curr.x - prev.x;
    const nextDirX = next.x - curr.x;
    
    // 检测X方向变向（符号变化）且变化幅度合理
    const isDirectionChange = currDirX * nextDirX < 0;
    const minChangeThreshold = 5; // 最小变化阈值
    
    if (isDirectionChange && Math.abs(currDirX) > minChangeThreshold) {
      // 计算击球前后的速度变化
      const beforeSpeed = prev.speed;
      const afterSpeed = next.speed;
      
      // 计算加速度
      const acceleration = Math.abs((afterSpeed - beforeSpeed) / (2 * frameInterval));
      
      // 过滤不合理的加速度值
      if (acceleration > 0 && acceleration < 100000) { // 设置合理范围
        hitEvents.push({
          frame: curr.frame,
          x: curr.x,
          y: curr.y,
          acceleration: acceleration,
          beforeSpeed: beforeSpeed,
          afterSpeed: afterSpeed,
          directionChange: Math.abs(currDirX)
        });
      }
    }
  }
  
  // 合并相近的击球事件（防止重复计算）
  const mergedEvents = [];
  let lastFrame = -100;
  
  hitEvents.forEach(event => {
    if (event.frame - lastFrame > 5) { // 至少间隔5帧
      mergedEvents.push(event);
      lastFrame = event.frame;
    }
  });
  
  return mergedEvents;
});

// 计算最大击球加速度
const maxHitAcceleration = computed(() => {
  return hitEvents.value.length > 0 
    ? Math.max(...hitEvents.value.map(e => e.acceleration)) 
    : 0;
});

// 计算平均击球加速度
const avgHitAcceleration = computed(() => {
  return hitEvents.value.length > 0 
    ? hitEvents.value.reduce((sum, e) => sum + e.acceleration, 0) / hitEvents.value.length 
    : 0;
});

// 过滤的异常数据数量
const filteredCount = computed(() => {
  if (!props.data?.xyFrameSpeedData || !props.data?.speedData) return 0;
  const points = props.data.xyFrameSpeedData;
  const speeds = props.data.speedData;
  const { filteredCount } = cleanData(points, speeds);
  return filteredCount;
});

const initChart = () => {
  if (!chartRef.value || hitEvents.value.length === 0) return;

  chartInstance = echarts.init(chartRef.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        if (!params || params.length === 0) return '';
        const data = params[0];
        return `第${data.data.frame}帧<br/>
                位置: (${data.data.x.toFixed(0)}, ${data.data.y.toFixed(0)})<br/>
                击球加速度: ${data.data.acceleration.toFixed(2)} 像素/秒²<br/>
                击球前速度: ${data.data.beforeSpeed.toFixed(2)} 像素/秒<br/>
                击球后速度: ${data.data.afterSpeed.toFixed(2)} 像素/秒`;
      }
    },
    legend: {
      data: ['击球加速度'],
      top: 10
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      name: '击球事件',
      data: hitEvents.value.map((_, index) => `击球${index + 1}`)
    },
    yAxis: {
      type: 'value',
      name: '加速度 (像素/秒²)',
      splitLine: {
        lineStyle: { type: 'dashed', opacity: 0.3 }
      }
    },
    series: [
      {
        name: '击球加速度',
        type: 'bar',
        data: hitEvents.value.map(e => ({
          value: e.acceleration,
          frame: e.frame,
          x: e.x,
          y: e.y,
          beforeSpeed: e.beforeSpeed,
          afterSpeed: e.afterSpeed
        })),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ff7875' },
            { offset: 1, color: '#ff4d4f' }
          ])
        },
        emphasis: {
          itemStyle: {
            color: '#ff1a1a'
          }
        },
        markLine: {
          data: [
            { type: 'average', name: '平均击球加速度' }
          ]
        }
      }
    ]
  };

  chartInstance.setOption(option);
};

const debounceResize = debounce(() => {
  chartInstance?.resize({ animation: { duration: 300 } });
}, 300);

onMounted(() => {
  initChart();
  window.addEventListener('resize', debounceResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', debounceResize);
  chartInstance?.dispose();
});

watch(() => props.data, () => {
  initChart();
}, { deep: true });
</script>

<template>
  <div class="chart-container">
    <h2>击球加速度分析</h2>
    <div ref="chartRef" class="chart"></div>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ hitEvents.length }}</div>
        <div class="stat-label">有效击球次数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ maxHitAcceleration.toFixed(2) }}</div>
        <div class="stat-label">最大击球加速度 (像素/秒²)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ avgHitAcceleration.toFixed(2) }}</div>
        <div class="stat-label">平均击球加速度 (像素/秒²)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ filteredCount }}</div>
        <div class="stat-label">过滤异常数据</div>
      </div>
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
}

.chart {
  width: 100%;
  height: 420px;
}

h2 {
  margin-left: 15px;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
  padding: 0 15px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.08);
  text-align: center;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #3182ce;
  margin-bottom: 5px;
}

.stat-label {
  color: #718096;
  font-size: 14px;
}
</style>