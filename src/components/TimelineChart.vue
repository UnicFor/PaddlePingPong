<!-- TimelineChart.vue -->
<template>
  <div class="chart-container full-width">
    <h2>时间轴轨迹回放</h2>
    <div ref="chart" class="chart">
      <div class="frame-background" :style="frameStyle"></div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  props: {
    chartData: {
      type: Object,
      required: true
    },
    frameDataList: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      chart: null,
      currentFrame: null
    };
  },
  computed: {
    frameStyle() {
      return this.currentFrame
        ? { backgroundImage: `url(${this.currentFrame})` }
        : {};
    }
  },
  watch: {
    chartData: {
      deep: true,
      handler() {
        this.updateChart();
      }
    }
  },
  mounted() {
    this.initChart();
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    this.chart?.dispose();
  },
  methods: {
    safeGetData(index) {
      return this.chartData.xyFrameSpeedData[index] || [0, 0, 0, 0];
    },
    initChart() {
      this.chart = echarts.init(this.$refs.chart);
      this.setupChartEvents();
      this.updateChart();
    },
    updateChart() {
      const options = this.chartData.frameData.map((frame, index) => ({
        title: { text: `球轨迹回放 - 第${frame}帧`, left: 'center' },
        series: [
          {
            name: '历史轨迹',
            type: 'scatter',
            data: this.chartData.xyFrameSpeedData.filter(p => p[2] <= frame),
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
            data: this.chartData.frameData,
            label: { formatter: value => `帧${value}` }
          },
          grid: { left: '5%', right: '5%', bottom: '15%' },
          xAxis: {
            type: 'value',
            min: this.chartData.xRange.min - 50,
            max: this.chartData.xRange.max + 50,
          },
          yAxis: {
            type: 'value',
            inverse: true,
            min: this.chartData.yRange.min - 50,
            max: this.chartData.yRange.max + 50,
          },
        },
        options: options
      };

      this.chart.setOption(option);
    },
    setupChartEvents() {
      this.chart.on('timelinechanged', params => {
        try {
          if (!this.frameDataList?.length) {
            this.currentFrame = '';
            return;
          }

          const maxIndex = Math.max(this.frameDataList.length - 1, 0);
          const safeIndex = Math.min(params.currentIndex, maxIndex);
          this.currentFrame = this.frameDataList[safeIndex] || '';

          this.$emit('frame-change', this.currentFrame);
        } catch (e) {
          console.error('帧更新错误:', e);
        }
      });
    },
    handleResize() {
      this.chart?.resize();
    }
  }
};
</script>