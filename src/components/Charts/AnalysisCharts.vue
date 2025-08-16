<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import Papa from 'papaparse';
import axios from 'axios';

import CombinedChart from "@/components/Charts/SpeedChart.vue";
import ScatterChart from "@/components/Charts/ScatterChart.vue";
import TimelineChart from "@/components/Charts/TimelineChart.vue";

import { useAuthStore } from '@/stores/auth';

const props = defineProps({
  videoId: {
    type: String,
    required: true
  }
});

// 开发者模式标志
const isDevMode = import.meta.env.DEV;

const auth = useAuthStore();
const stats = ref([]);
const processedData = ref(null);
const frameDataList = ref([]);
const currentFrameIndex = ref(0);

const setupAxiosInterceptor = () => {
  axios.interceptors.request.use(config => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${auth.token}`;
    }
    return config;
  }, error => {
    return Promise.reject(error);
  });

  axios.interceptors.response.use(response => response, error => {
    if (error.response?.status === 401) {
      // router.push('/login');
    }
    return Promise.reject(error);
  });
};

const loadCSVData = async () => {
  if (isDevMode) {
    // 开发者模式
    try {
      const response = await fetch('/src/assets/test-data/ball-data.csv');
      const csvText = await response.text();
      
      return new Promise((resolve) => {
        Papa.parse(csvText, {
          header: true,
          dynamicTyping: true,
          complete: (results) => {
            resolve(results.data.filter(row =>
              row.Frame !== null &&
              !isNaN(row.X) &&
              !isNaN(row.Y)
            ));
          }
        });
      });
    } catch (error) {
      console.error('加载本地CSV数据失败:', error);
      throw error;
    }
  } else {
    // 生产模式
    try {
      const response = await fetch(`/api/ball-data/${props.videoId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('jwt_token')}`,
          'Content-Type': 'text/csv'
        }
      });
      const csvText = await response.text();
      
      return new Promise((resolve) => {
        Papa.parse(csvText, {
          header: true,
          dynamicTyping: true,
          complete: (results) => {
            resolve(results.data.filter(row =>
              row.Frame !== null &&
              !isNaN(row.X) &&
              !isNaN(row.Y)
            ));
          }
        });
      });
    } catch (error) {
      console.error('加载API CSV数据失败:', error);
      throw error;
    }
  }
};

const processData = (rawData) => {
  // 初始化各类数据数组
  const frameData = [];
  const xData = [];
  const yData = [];
  const speedData = [];
  const validPoints = [];
  const xyConnectedData = [];

  // 遍历原始数据
  rawData.forEach((row) => {
    frameData.push(Number(row.Frame));

    if (!isNaN(row.X) && !isNaN(row.Y)) {
      // 添加有效坐标到X、Y数据数组
      xData.push(row.X);
      yData.push(row.Y);
      
      // 处理速度数据：如果速度为NaN，则设为0，但保留坐标点
      const validSpeed = !isNaN(row.Speed) ? row.Speed : 0;
      validPoints.push([row.X, row.Y, row.Frame, validSpeed]);
    } else {
      // 如果X或Y为NaN，标记为无效数据
      xData.push(null);
      yData.push(null);
    }

    // 速度数据单独处理：NaN速度会被设为null
    speedData.push(!isNaN(row.Speed) ? row.Speed : null);
  });

  // 生成轨迹连接线数据：连接相邻的有效点
  for (let i = 0; i < validPoints.length - 1; i++) {
    xyConnectedData.push([validPoints[i][0], validPoints[i][1]]);
    xyConnectedData.push([validPoints[i+1][0], validPoints[i+1][1]]);
    xyConnectedData.push([null, null]);
  }

  // 计算统计信息
  const validSpeeds = speedData.filter(s => s !== null);
  const maxSpeed = validSpeeds.length > 0 ? Math.max(...validSpeeds) : 0;
  const avgSpeed = validSpeeds.length > 0 
    ? validSpeeds.reduce((a, b) => a + b, 0) / validSpeeds.length 
    : 0;
  
  // 有效坐标数
  let validCoords = validPoints.reduce((count, item) => {
    if (item[3] !== 0) {
      count++;
    }
    return count;
  }, 0);
  
  const totalFrames = rawData.length;
  const detectionRate = ((validCoords / totalFrames) * 100).toFixed(2);

  // 计算X和Y的极差来判断拍摄方向
  const xRange = Math.max(...validPoints.map(p => p[0])) - Math.min(...validPoints.map(p => p[0]));
  const yRange = Math.max(...validPoints.map(p => p[1])) - Math.min(...validPoints.map(p => p[1]));
  
  // 判断拍摄方向
  let shootingDirection = '斜角拍摄(误差较大)';
  const rangeRatio = xRange / yRange;
  
  if (rangeRatio > 1.5) {
    shootingDirection = '正对长边';
  } else if (rangeRatio < 0.67) {
    shootingDirection = '正对短边';
  }

  return {
    frameData,
    xData,
    yData,
    speedData,
    xyFrameSpeedData: validPoints,
    xyConnectedData,
    stats: {
      maxSpeed: maxSpeed.toFixed(2),
      avgSpeed: avgSpeed.toFixed(2),
      validCoords,
      totalFrames,
      detectionRate: detectionRate,
      shootingDirection: shootingDirection,
      xRange: xRange.toFixed(2),
      yRange: yRange.toFixed(2)
    },
    xRange: {
      min: Math.min(...validPoints.map(p => p[0])),
      max: Math.max(...validPoints.map(p => p[0]))
    },
    yRange: {
      min: Math.min(...validPoints.map(p => p[1])),
      max: Math.max(...validPoints.map(p => p[1]))
    }
  };
};

const createStats = (stats) => {
  return [
    { value: stats.maxSpeed, label: '最大速度 (像素/秒)' },
    { value: stats.avgSpeed, label: '平均速度 (像素/秒)' },
    { value: stats.validCoords, label: '有效坐标数' },
    { value: stats.totalFrames, label: '总有效帧数' },
    { value: `${stats.detectionRate}%`, label: '球检测率' },
    { value: stats.shootingDirection, label: '拍摄方向' }
  ];
};

const handleFrameChange = (index) => {
  currentFrameIndex.value = index;
};

const initData = async () => {
  try {
    setupAxiosInterceptor();
    const [csvData] = await Promise.all([loadCSVData()]);
    
    processedData.value = processData(csvData);
    stats.value = createStats(processedData.value.stats);
  } catch (error) {
    console.error('初始化失败:', error);
  }
};

onMounted(() => {
  initData();
});

onUnmounted(() => {
  // 清理工作
});
</script>

<template>
  <div class="analysis-container">
    <div class="container">
      <div class="stats">
        <div v-for="stat in stats" :key="stat.label" class="stat-card">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>

      <div class="dashboard">
        <CombinedChart :data="processedData" />
        <ScatterChart :data="processedData" />
        <TimelineChart 
          :data="processedData" 
          :frame-data-list="frameDataList"
          :current-frame-index="currentFrameIndex"
          @update:current-frame-index="handleFrameChange"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-container {
  height: 100%;
  overflow-y: auto;
}

.container {
  max-width: 1440px;
  margin: 20px auto;
  padding: 0 15px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.08);
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #3182ce;
}

.stat-label {
  color: #718096;
  font-size: 14px;
}

.dashboard {
  display: grid;
  grid-template-columns: 1fr;
  margin-top: 20px;
  gap: 20px;
  min-width: 400px;
}
</style>