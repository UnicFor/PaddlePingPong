<template>
  <div class="chart-container">
    <div ref="chart" style="width: 100%; height: 100%"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

function gaussianRandom(mean = 50, stdev = 15) {
  const u = 1 - Math.random()
  const v = Math.random()
  const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v)
  return Math.min(100, Math.max(0, Math.round(z * stdev + mean)))
}

export default {
  name: 'ServerChart',
  props: {
    title: {
      type: String,
      default: '服务器负载趋势'
    }
  },
  data() {
    return {
      chart: null,
      dataPoints: [],
      baseline: 50,
      stabilityCounter: 0,
      currentTrend: 0
    }
  },
  mounted() {
    this.initChart()
    this.startSimulation()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    this.chart?.dispose()
    clearInterval(this.interval)
  },
  methods: {
    initChart() {
      this.chart = echarts.init(this.$refs.chart)
      this.setBaseOption()
    },
    generateSmartData() {
      // 每10次调整一次基准值
      if (this.stabilityCounter++ > 10) {
        this.stabilityCounter = 0
        // 随机生成新的基准值（限制变化幅度）
        this.baseline = Math.min(80, Math.max(20,
          this.baseline + (Math.random() > 0.5 ? 15 : -15)
        ))
        // 设置趋势方向
        this.currentTrend = Math.random() > 0.5 ? 1 : -1
      }

      // 生成带趋势的波动值
      let variation
      if (this.stabilityCounter < 3) { // 趋势变化阶段
        variation = this.currentTrend * (5 + Math.random() * 10)
      } else { // 稳定波动阶段
        variation = gaussianRandom(0, 3) // 小范围波动
      }

      // 应用平滑变化
      const newValue = Math.min(100, Math.max(0,
        this.baseline + variation + gaussianRandom(0, 2)
      ))

      return Math.round(newValue)
    },

    startSimulation() {
      // 初始化数据
      this.dataPoints = Array.from({length: 30}, () => this.generateSmartData())

      this.interval = setInterval(() => {
        this.stabilityCounter++
        const newValue = this.generateSmartData()
        this.dataPoints = [...this.dataPoints.slice(1), newValue]

        this.chart.setOption({
          xAxis: { data: this.generateTimeLabels() },
          series: [{ data: this.dataPoints }]
        })
      }, 2000)
    },
    setBaseOption() {
      const option = {
        title: {
          top: 10,
          left: 'center',
          text: `当前服务器负载`,
          textStyle: {
            fontSize: 20,
            color: '#2d3748'
          }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#fff',
          borderColor: '#e4e7ed',
          borderWidth: 1,
          textStyle: {
            color: '#606266'
          },
          axisPointer: {
            type: 'line',
            lineStyle: {
              color: '#409EFF',
              type: 'dashed'
            }
          }
        },
        grid: {
          left: '4%',
          right: '6%',
          bottom: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: this.generateTimeLabels(),
          axisLine: {
            lineStyle: {
              color: '#dcdfe6'
            }
          },
          axisLabel: {
            color: '#909399'
          }
        },
        yAxis: {
          type: 'value',
          max: 100,
          axisLine: {
            show: false
          },
          splitLine: {
            lineStyle: {
              color: '#ebeef5',
              type: 'dashed'
            }
          },
          axisLabel: {
            color: '#909399',
            formatter: '{value}%'
          }
        },
        series: [{
          name: 'CPU使用率',
          type: 'line',
          smooth: true,
          symbol: 'none',
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#a0cfff' },
              { offset: 1, color: '#ecf5ff' }
            ])
          },
          lineStyle: {
            width: 2,
            color: '#409EFF'
          },
          data: this.dataPoints
        }]
      }
      this.chart.setOption(option)
    },
    generateTimeLabels() {
      const now = new Date()
      return Array.from({length: 30}, (_, i) => {
        const time = new Date(now.getTime() - (29 - i) * 2000)
        return time.toLocaleTimeString('zh', { hour12: false })
      })
    }
  }
}
</script>

<style scoped>
.chart-container {
  height: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);

}
</style>