<script setup>
import * as echarts from 'echarts';
import { onMounted, onUnmounted, ref, watch, computed } from 'vue';
import { processFittingData, polynomialFit } from '@/utils/dataFitting.js';

const props = defineProps({
	data: {
		type: Object,
		required: true
	},
	fitDegree: {
		type: Number,
		default: 20
	}
});

const chartRef = ref(null);
let chartInstance = null;

const debounce = (func, delay) => {
	let timeoutId
	return (...args) => {
		if(timeoutId) 
			clearTimeout(timeoutId)
		timeoutId = setTimeout(() => {
			func(...args)
		}, delay)
	}
}

// 处理所有数据
const processedData = computed(() => 
	processFittingData(props.data, props.fitDegree)
);

const initChart = () => {
	if (!chartRef.value || !processedData.value) return;

	chartInstance = echarts.init(chartRef.value);
	
	const option = {
		tooltip: {
			trigger: 'axis',
			axisPointer: { 
				type: 'cross',
				label: { backgroundColor: '#6a7985' }
			},
			formatter: params => {
				let result = `第${params[0].axisValue}帧<br/>`;
				params.forEach(p => {
					if (p.value != null && !isNaN(p.value)) {
						const value = typeof p.value === 'number' ? p.value.toFixed(2) : p.value;
						result += `${p.seriesName}: ${value}<br/>`;
					}
				});
				return result;
			}
		},
		legend: { 
			data: ['X坐标', 'Y坐标', '速度 (原始)', '速度 (拟合)'],
			top: 10,
			textStyle: { fontSize: 12 },
			selected: {
				'速度 (原始)': true,
				'速度 (拟合)': true
			}
		},
		grid: [
			{ left: '10%', right: '8%', top: '60px', height: '52%' },
			{ left: '10%', right: '8%', top: '66%', height: '0%' }
		],
		xAxis: [
			{ 
				type: 'category', 
				data: processedData.value.frameData, 
				gridIndex: 0,
				axisLabel: { show: false },
				axisLine: { lineStyle: { color: '#ccc' } }
			},
			{ 
				type: 'category', 
				data: processedData.value.frameData, 
				gridIndex: 1,
				name: '帧数',
				nameLocation: 'middle',
				nameGap: 25,
				axisLine: { lineStyle: { color: '#666' } }
			}
		],
		yAxis: [
			{ 
				type: 'value', 
				name: '坐标 (像素)',
				nameLocation: 'middle',
				nameGap: 40,
				gridIndex: 0,
				splitLine: { 
					show: true,
					lineStyle: { type: 'dashed', opacity: 0.3 }
				},
				axisLine: { lineStyle: { color: '#666' } }
			},
			{ 
				type: 'value', 
				name: '速度 (像素/秒)',
				nameLocation: 'middle',
				nameGap: 50,
				gridIndex: 1,
				splitLine: { 
					show: true,
					lineStyle: { type: 'dashed', opacity: 0.3 }
				},
				axisLine: { lineStyle: { color: '#666' } }
			}
		],
		series: [
			{
				name: 'X坐标',
				type: 'line',
				data: processedData.value.xOriginal,
				symbol: 'circle',
				symbolSize: 6,
				lineStyle: { 
					color: '#5470c6',
					width: 2
				},
				areaStyle: {
					color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
						{ offset: 0, color: 'rgba(84, 112, 198, 0.2)' },
						{ offset: 1, color: 'rgba(84, 112, 198, 0.02)' }
					])
				}
			},
			{
				name: 'Y坐标',
				type: 'line',
				data: processedData.value.yOriginal,
				symbol: 'circle',
				symbolSize: 6,
				lineStyle: { 
					color: '#91cc75',
					width: 2
				},
				areaStyle: {
					color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
						{ offset: 0, color: 'rgba(145, 204, 117, 0.2)' },
						{ offset: 1, color: 'rgba(145, 204, 117, 0.02)' }
					])
				}
			},
			{
				name: '速度 (原始)',
				type: 'line',
				data: processedData.value.speedOriginal,
				symbol: 'circle',
				symbolSize: 6,
				itemStyle: {
					color: '#000',
					opacity: 0.6
				},
				lineStyle: { 
					color: '#000',
					width: 2,
					type: 'dashed',
					opacity: 0.5
				}
			},
			{
				name: '速度 (拟合)',
				type: 'line',
				data: processedData.value.speedFitted,
				symbol: 'none',
				itemStyle: {
					color: '#ff7875',
				},
				lineStyle: { 
					color: '#ff7875',
					width: 3
				},
				areaStyle: {
					color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
						{ offset: 0, color: 'rgba(255, 120, 117, 0.3)' },
						{ offset: 1, color: 'rgba(255, 120, 117, 0.05)' }
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
				bottom: 0,
				height: 30,
				top: '80%',
				borderColor: '#ccc',
				fillerColor: 'rgba(84, 112, 198, 0.2)',
				handleStyle: {
					color: '#5470c6'
				}
			},
			{
				type: 'inside',
				xAxisIndex: [0, 1],
				start: 0,
				end: 100
			}
		],
		toolbox: {
			feature: {
				dataZoom: {
					yAxisIndex: 'none'
				},
				restore: {},
				saveAsImage: {}
			},
			right: 15,
			top: 10
		}
	};

	chartInstance.setOption(option);
};

const debounceResize = debounce(() => {
	chartInstance?.resize({ animation: { duration: 300 } })
}, 300)

const debouncedInitChart = debounce(() => {
	if (chartInstance && processedData.value) {
		initChart()
	}
}, 300)

onMounted(() => {
	initChart();
	window.addEventListener('resize', debounceResize)
});

onUnmounted(() => {
	window.removeEventListener('resize', debounceResize);
	chartInstance?.dispose();
});

watch(() => props.data, () => {
	initChart();
}, { deep: true });

watch(() => props.fitDegree, () => {
	initChart();
});
</script>

<template>
	<div class="chart-container">
		<h2>球速拟合图 (可筛选时间段)</h2>
		<div ref="chartRef" class="chart"></div>
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
</style>