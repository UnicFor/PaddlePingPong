<template>
  <div ref="chartContainer" class="commit-heatmap"></div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  props: {
    year: {
      type: Number,
      default: new Date().getFullYear()
    },
  },
  data() {
    return {
      myChart: null,
      chartData: []
    };
  },
  mounted() {
    this.chartData = this.generateYearData();
    this.$nextTick(() => {
      this.initChart();
    });
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize);
    this.disposeChart();
  },
  methods: {
    initChart() {
      this.disposeChart();
      if (!this.$refs.chartContainer) return;

      this.myChart = echarts.init(this.$refs.chartContainer);

      const option = {
        title: {
          top: 10,
          left: 'center',
          text: `${this.year} 提交记录`,
          textStyle: {
            fontSize: 28,
            color: '#2d3748'
          }
        },
        tooltip: {
          formatter: params =>
            `${params.value[0]}<br/>提交次数: ${params.value[1]}`
        },
        visualMap: {
          min: 0,
          max: 20,
          type: 'piecewise',
          orient: 'horizontal',
          left: 'center',
          top: 60,
          pieces: [ // 手动定义色块分段
            { min: 0, max: 0, color: '#f0f9ff' },
            { min: 1, max: 5, color: '#a0c8f0' },
            { min: 6, max: 10, color: '#63a4e3' },
            { min: 11, max: 20, color: '#3182ce' }
          ],
          textStyle: {
            color: '#666'    // 统一文字颜色
          },
          selectedMode: false,
        },
        calendar: {
        top: 120,
        left: '10%', right: '6%',
        cellSize: ['auto', 12],
        range: `${this.year}`,
        itemStyle: {
          borderWidth: 0.5,
          color: '#f8fafc'
        },
        dayLabel: {
          firstDay: 1,
          fontSize: 12,
          color: '#666',
          nameMap: ['周日 ', '周一 ', '周二 ', '周三 ', '周四 ', '周五 ', '周六 ']
        },
        monthLabel: {
          nameMap: 'ZH',
          color: '#666',
          fontSize: 12,
          margin: 8
        },
        splitLine: {
          lineStyle: {
            color: '#616161',
            width: 0.5
          }
        },
        yearLabel: {
          show: false
        }
      },
        series: {
          type: 'heatmap',
          coordinateSystem: 'calendar',
          data: this.chartData,
          progressive: 400,
          blurSize: 8,
          itemStyle: {
            borderRadius: 4,

          },
          emphasis: {
            itemStyle: {
              borderColor: '#333',
              borderWidth: 1
            }
          }
        }
      };

      option && this.myChart.setOption(option);
    },

    // 图表销毁方法
    disposeChart() {
      if (this.myChart) {
        this.myChart.dispose();
        this.myChart = null;
      }
    },
    // resize处理函数
    handleResize() {
      // 使用防抖避免频繁触发
      clearTimeout(this.resizeTimer);
      this.resizeTimer = setTimeout(() => {
        if (this.myChart) {
          this.myChart.resize();
        }
      }, 60);
    },

    generateYearData() {
      // 生成固定随机数据（只执行一次）
      const fixedData = [];
      const now = new Date();

      // 生成全年数据模板
      const start = +new Date(`${this.year}-01-01`);
      const end = +new Date(`${this.year + 1}-01-01`);
      const dayTime = 3600 * 24 * 1000;

      // 创建全年空数据
      for (let time = start; time < end; time += dayTime) {
        fixedData.push([
          echarts.time.format(time, '{yyyy}-{MM}-{dd}', false),
          0
        ]);
      }

      // 生成固定随机数（使用种子确保一致性）
      const seed = this.year;
      for (let i = 0; i < 24; i++) {
        const d = new Date(now);
        d.setDate(now.getDate() - i);
        const dateStr = echarts.time.format(d, '{yyyy}-{MM}-{dd}', false);
        const index = fixedData.findIndex(item => item[0] === dateStr);
        if (index !== -1) {
          const pseudoRandom = Math.abs(Math.sin(seed + i)) * 20; // 伪随机生成
          fixedData[index][1] = Math.floor(pseudoRandom);
        }
      }
      return fixedData;
    }
  },
};
</script>

<style scoped>
.commit-heatmap {
  height: 260px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>