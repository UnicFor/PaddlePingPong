<template>
  <div ref="chartContainer" style="width: 100%; height: 300px;"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  angles: {
    type: Object,
    required: true
  }
})

const chartContainer = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartContainer.value) return

  chartInstance = echarts.init(chartContainer.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}°'
    },
    legend: {
      data: ['左肘角度', '右肘角度', '身体扭转']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['平均动作角度']
    },
    yAxis: {
      type: 'value',
      name: '角度(°)',
      min: 0,
      max: 180,
      axisLabel: {
        formatter: '{value}°'
      }
    },
    series: [
      {
        name: '左肘角度',
        type: 'bar',
        data: [props.angles.leftElbowAngle || 0],
        itemStyle: {
          color: '#3498db'
        },
        markLine: {
          data: [
            { yAxis: 90, name: '最佳角度', lineStyle: { color: 'green' } }
          ]
        }
      },
      {
        name: '右肘角度',
        type: 'bar',
        data: [props.angles.rightElbowAngle || 0],
        itemStyle: {
          color: '#e74c3c'
        }
      },
      {
        name: '身体扭转',
        type: 'bar',
        data: [props.angles.torsoRotationAngle || 0],
        itemStyle: {
          color: '#9b59b6'
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

onMounted(initChart)
onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(() => props.angles, updateChart, { deep: true })
</script>