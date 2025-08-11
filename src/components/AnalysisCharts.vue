<template>
  <div class="analysis-container">
    <div class="container">
      <div class="stats">
        <div v-for="stat in stats" :key="stat.label" class="stat-card">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>

      <div class="angle-analysis-section">
        <div class="angle-chart-container">
          <h2>关键角度分析</h2>
          <AngleChart :angles="currentAngles" />
        </div>
        <div class="angle-data-container">
          <h2>角度数据表</h2>
          <AngleDataDisplay :angles="currentAngles" />
        </div>
        <div class="angle-controls">
          <div class="slider-container">
            <input
              type="range"
              v-model.number="currentFrameIndex"
              :min="0"
              :max="maxFrameIndex"
              class="angle-slider"
              @input="handleAngleFrameChange"
            >
          </div>
        </div>
      </div>

      <div class="dashboard">
        <div class="chart-container">
          <h2>轨迹与速度组合图</h2>
          <div ref="combinedChart" class="chart"></div>
        </div>

        <div class="chart-container">
          <h2>球轨迹散点图</h2>
          <div ref="scatterChart" class="chart"></div>
        </div>

        <div class="chart-container full-width">
          <h2>时间轴轨迹回放</h2>
          <div ref="timelineChart" class="chart">
            <div class="frame-background" :style="frameStyle"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import Papa from 'papaparse';
import axios from 'axios';

import AngleChart from "@/components/AngleChart.vue";
import AngleDataDisplay from "@/components/AngleDataDisplay.vue";

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

export default {
  name: 'AnalysisCharts',
  components: {AngleDataDisplay, AngleChart},
  props: {
    videoId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      stats: [],
      charts: {
        combined: null,
        scatter: null,
        timeline: null,
      },
      currentFrameIndex: 0,
      maxFrameIndex: 0,
      frameDataList: [],
      currentFrame: null,
      processedData: null,

      currentAngles: {},
      poseData: null
    };
  },
  computed: {
    maxFrameIndex() {
      return this.processedData ? this.processedData.frameData.length - 1 : null
    },
    frameStyle() {
      return this.currentFrame
        ? { backgroundImage: `url(${this.currentFrame})` }
        : {};
    }
  },
  async mounted() {
    this.setupAxiosInterceptor();
    await this.initCharts();
    window.addEventListener('resize', this.handleResize);
    window.debugAngles = () => {
      console.log('当前角度数据:', this.currentAngles);
      console.log('骨骼数据:', this.poseData);
      console.log('当前帧索引:', this.currentFrameIndex);
    }
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    Object.values(this.charts).forEach(chart => chart?.dispose());
  },
  methods: {
    calculateKeyAngles(keyPointMap) {
      const angles = {};

      // 左肘角度计算
      if (keyPointMap['left_shoulder'] && keyPointMap['left_elbow'] && keyPointMap['left_wrist']) {
        angles.leftElbowAngle = this.calculateBendAngle(
          keyPointMap['left_shoulder'].position,
          keyPointMap['left_elbow'].position,
          keyPointMap['left_wrist'].position
        );
      }

      // 右肘角度计算
      if (keyPointMap['right_shoulder'] && keyPointMap['right_elbow'] && keyPointMap['right_wrist']) {
        angles.rightElbowAngle = this.calculateBendAngle(
          keyPointMap['right_shoulder'].position,
          keyPointMap['right_elbow'].position,
          keyPointMap['right_wrist'].position
        );
      }

      // 身体扭转角度计算
      if (keyPointMap['left_shoulder'] && keyPointMap['right_shoulder'] &&
          keyPointMap['left_hip'] && keyPointMap['right_hip']) {
        const shoulderAngle = this.calculateAngle(
          keyPointMap['left_shoulder'].position,
          keyPointMap['right_shoulder'].position
        );
        const hipAngle = this.calculateAngle(
          keyPointMap['left_hip'].position,
          keyPointMap['right_hip'].position
        );
        let torsoRotation = Math.abs(shoulderAngle - hipAngle);
        if (torsoRotation > 200) {
          torsoRotation = Math.abs(torsoRotation - 360);  // 超过200度时取补角
        }
        angles.torsoRotationAngle = Math.min(torsoRotation, 80.4)
      }

      return angles;
    },

    calculateAngle(p1, p2) {
      const deltaY = p2[1] - p1[1];
      const deltaX = p2[0] - p1[0];
      return Math.atan2(deltaY, deltaX) * (180 / Math.PI);
    },

    calculateBendAngle(p1, p2, p3) {
      const vec1 = [p1[0] - p2[0], p1[1] - p2[1]];
      const vec2 = [p3[0] - p2[0], p3[1] - p2[1]];
      const dotProduct = vec1[0] * vec2[0] + vec1[1] * vec2[1];
      const mag1 = Math.sqrt(vec1[0] ** 2 + vec1[1] ** 2);
      const mag2 = Math.sqrt(vec2[0] ** 2 + vec2[1] ** 2);
      return Math.acos(Math.max(-1, Math.min(1, dotProduct / (mag1 * mag2)))) * (180 / Math.PI);
    },
    handleAngleFrameChange() {
      // 更新图表实例的当前帧
      if (this.charts.timeline) {
        this.charts.timeline.dispatchAction({
          type: 'timelineChange',
          currentIndex: this.currentFrameIndex
        });
      }
      this.updateAnglesForCurrentFrame();
    },

    // 修改safeGetData方法
    safeGetData(index) {
      this.currentFrameIndex = index; // 必须先更新索引
      this.updateAnglesForCurrentFrame();
      return this.processedData.xyFrameSpeedData[index] || [0, 0, 0, 0];
    },

    setupAxiosInterceptor() {
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
          this.$router.push('/login');
        }
        return Promise.reject(error);
      });
    },

    async initCharts() {
      try {
        const csvData = await this.loadCSVData();
        await this.loadFrameData();

        this.poseData = await this.loadPoseData();

        this.processedData = this.processData(csvData);
        this.stats = this.createStats(this.processedData.stats);
        this.initChartInstances();

        // 处理骨骼数据
        this.updateAnglesForCurrentFrame();
      } catch (error) {
        console.error('初始化失败:', error);
        Notification.error({
          title: '错误',
          message: '数据加载失败',
          duration: 3000
        });
      }
    },

    async loadCSVData() {
      try {
        const response = await fetch(`/api/ball-data/${this.videoId}`, {
          headers: {
            Authorization: `Bearer ${auth.token}`,
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
                !isNaN(row.Y) &&
                !isNaN(row.Speed)
              ))
            }
          });
        });
      } catch (error) {
        console.error('加载CSV数据失败:', error);
        throw error;
      }
    },

    async loadFrameData() {
      try {
        const response = await fetch(`/api/frames-batch/${this.videoId}`, {
          headers: { Authorization: `Bearer ${auth.token}` }
        });

        const data = await response.json();
        this.frameDataList = data.frames;
        return data.frames;
      } catch (error) {
        console.error('加载帧数据失败:', error);
        this.frameDataList = [];
        throw error;
      }
    },

    async loadPoseData() {
      try {
        const response = await fetch(`/api/pose-data/${this.videoId}`, {
          headers: { Authorization: `Bearer ${auth.token}` }
        });
        const res = await response.json();

        return {
          meta_info: res.data.meta_info,
          instance_info: res.data.instance_info.map(frame => ({
            frame_id: Number(frame.frame_id),
            instances: frame.instances.map(inst => ({
              bbox: inst.bbox,
              keypoints: inst.keypoints,
              keypoint_scores: inst.keypoint_scores
            }))
          }))
        };
      } catch (error) {
        console.error('加载骨骼数据失败:', error);
        return null;
      }
    },

    updateAnglesForCurrentFrame() {
      if (!this.poseData) return;

      const frameData = this.poseData.instance_info.find(
        f => f.frame_id === this.processedData.frameData[this.currentFrameIndex]
      );

      if (frameData?.instances?.[0]?.keypoints) {
        const keyPointMap = {};
        const keyPointNames = this.poseData.meta_info.keypoint_id2name || {};

        frameData.instances[0].keypoints.forEach((kpt, idx) => {
          if (keyPointNames[idx]) {
            keyPointMap[keyPointNames[idx]] = {
              position: kpt,
              score: frameData.instances[0].keypoint_scores[idx]
            };
          }
        });

        this.currentAngles = this.calculateKeyAngles(keyPointMap);
      }
    },

    processData(rawData) {
      const frameData = [];
      const xData = [];
      const yData = [];
      const speedData = [];
      const validPoints = [];
      const xyConnectedData = [];

      rawData.forEach((row) => {
        frameData.push(Number(row.Frame));

        if (!isNaN(row.X) && !isNaN(row.Y)) {
          xData.push(row.X);
          yData.push(row.Y);
          validPoints.push([row.X, row.Y, row.Frame, row.Speed || 0]);
        } else {
          xData.push(null);
          yData.push(null);
        }

        speedData.push(!isNaN(row.Speed) ? row.Speed : null);
      });

      // 生成连接线数据
      for (let i = 0; i < validPoints.length - 1; i++) {
        xyConnectedData.push([validPoints[i][0], validPoints[i][1]]);
        xyConnectedData.push([validPoints[i+1][0], validPoints[i+1][1]]);
        xyConnectedData.push([null, null]);
      }

      // 计算统计信息
      const validSpeeds = speedData.filter(s => s !== null);
      const maxSpeed = Math.max(...validSpeeds);
      const avgSpeed = validSpeeds.reduce((a, b) => a + b, 0) / validSpeeds.length;
      const validCoords = validPoints.length;
      const totalFrames = rawData.length;

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
          detectionRate: ((validCoords / totalFrames) * 100).toFixed(2)
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
    },

    createStats(stats) {
      return [
        { value: stats.maxSpeed, label: '最大速度 (像素/秒)' },
        { value: stats.avgSpeed, label: '平均速度 (像素/秒)' },
        { value: stats.validCoords, label: '有效坐标数' },
        { value: stats.totalFrames, label: '总有效帧数' },
        { value: `${stats.detectionRate}%`, label: '球检测率' }
      ];
    },

    initChartInstances() {
      this.charts.combined = this.createCombinedChart();
      this.charts.scatter = this.createScatterChart();
      this.charts.timeline = this.createTimelineChart();
    },

    createCombinedChart() {
      const chart = echarts.init(this.$refs.combinedChart);
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          formatter: params => {
            let result = `第${params[0].axisValue}帧<br/>`;
            params.forEach(p => {
              if (p.value != null) {
                result += `${p.seriesName}: ${p.seriesType === 'bar' ? p.value.toFixed(2) : p.value}<br/>`;
              }
            });
            return result;
          }
        },
        legend: { data: ['X坐标', 'Y坐标', '速度'] },
        grid: [
          { left: '10%', right: '4%', top: '60px', height: '50%' },
          { left: '6%', right: '4%', top: '62%', height: '24%' }
        ],
        xAxis: [
          { type: 'category', data: this.processedData.frameData, gridIndex: 0, axisLabel: { show: false } },
          { type: 'category', data: this.processedData.frameData, gridIndex: 1 }
        ],
        yAxis: [
          { type: 'value', name: '坐标', gridIndex: 0, splitLine: { show: false } },
          { type: 'value', name: '速度 (像素/秒)', gridIndex: 1, splitLine: { show: false } }
        ],
        series: [
          {
            name: 'X坐标',
            type: 'line',
            data: this.processedData.xData,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: { color: '#5470c6' }
          },
          {
            name: 'Y坐标',
            type: 'line',
            data: this.processedData.yData,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: { color: '#91cc75' }
          },
          {
            name: '速度',
            type: 'bar',
            data: this.processedData.speedData,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 1, color: '#188df0' }
              ])
            }
          }
        ],
        dataZoom: [
          {
            type: 'slider',
            xAxisIndex: [0, 1],
            start: 0,
            end: 100,
            bottom: 5
          }
        ]
      };
      chart.setOption(option);
      return chart;
    },

    createScatterChart() {
      const chart = echarts.init(this.$refs.scatterChart);
      const scatterData = this.processedData.xyFrameSpeedData.map(p => [p[0], p[1], p[2], p[3]]);
      const maxSpeed = Math.max(...this.processedData.speedData.filter(s => s !== null));

      const option = {
        tooltip: {
          formatter: params => `帧: ${params.value[2]}<br/>坐标: (${params.value[0].toFixed(1)}, ${params.value[1].toFixed(1)})<br/>速度: ${params.value[3].toFixed(2)} 像素/秒`
        },
        xAxis: {
          type: 'value',
          min: this.processedData.xRange.min - 50,  // 添加50像素缓冲
          max: this.processedData.xRange.max + 50,
          axisLabel: {
            formatter: value => value.toFixed(0)   // 优化标签显示
          }
        },
        yAxis: {
          type: 'value',
          inverse: true,
          min: this.processedData.yRange.min - 50,
          max: this.processedData.yRange.max + 50,
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
            data: this.processedData.xyConnectedData,
            lineStyle: { opacity: 0.5 },
            showSymbol: false
          }
        ]
      };
      chart.setOption(option);
      return chart;
    },

    createTimelineChart() {
      const chart = echarts.init(this.$refs.timelineChart);
      const options = this.processedData.frameData.map((frame, index) => ({
        title: { text: `球轨迹回放 - 第${frame}帧`, left: 'center' },
        series: [
          {
            name: '历史轨迹',
            type: 'scatter',
            data: this.processedData.xyFrameSpeedData.filter(p => p[2] <= frame),
            symbolSize: 10,
            itemStyle: { color: '#91cc75', opacity: 0.5 }
          },
          {
            name: '当前位置',
            type: 'effectScatter',
            data: [this.safeGetData(index)],
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
            data: this.processedData.frameData,
            label: { formatter: value => `帧${value}` }
          },
          grid: { left: '5%', right: '5%', bottom: '25%' },
          xAxis: {
            type: 'value',
            min: this.processedData.xRange.min - 50,
            max: this.processedData.xRange.max + 50,
          },
          yAxis: {
            type: 'value',
            inverse: true,
            min: this.processedData.yRange.min - 50,
            max: this.processedData.yRange.max + 50,
          },
        },
        options: options
      };

      chart.on('timelinechanged', params => {
      try {
        // 添加空数组检查
        if (!this.frameDataList || this.frameDataList.length === 0) {
          this.currentFrame = '';
          return;
        }

        // 确保索引在有效范围内
        const maxAllowedIndex = Math.max(this.frameDataList.length - 1, 0);
        const safeIndex = Math.min(params.currentIndex, maxAllowedIndex);
        const finalIndex = Math.max(safeIndex, 0);

        this.currentFrame = this.frameDataList[finalIndex] || '';
      } catch (e) {
        console.error('帧更新错误:', e);
      }
    });

      chart.setOption(option);
      return chart;
    },

    handleResize() {
      Object.values(this.charts).forEach(chart => {
        chart.resize({
          animation: {duration: 300}
        });
      })
    }
  }
};
</script>

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

.angle-controls {
  grid-column: 1 / -1;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.slider-container {
  position: relative;
  padding: 20px 30px;
}

.angle-slider {
  width: 100%;
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  outline: none;
}

.angle-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  background: #3182ce;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s;
}

.angle-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
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

.angle-analysis-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.angle-chart-container,
.angle-data-container {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.angle-chart-container h2,
.angle-data-container h2 {
  margin-bottom: 15px;
  color: #2c3e50;
  font-size: 16px;
}

.dashboard {
  display: grid;
  grid-template-columns: 1fr;
  margin-top: 20px;
  gap: 20px;
  min-width: 400px;
}

.chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  padding: 15px 0 0 0;
  transition: transform 0.3s;
  min-width: 400px;
}

.chart-container h2 {
  margin-left: 15px;
}

.chart {
  width: 100%;
  height: 400px;
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
  z-index: 0;
}
</style>