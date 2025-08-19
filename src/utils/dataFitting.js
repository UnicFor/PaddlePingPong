/**
 * 数据拟合工具模块
 * 多项式曲线拟合、数据清洗
 */

/**
 * 处理数据中的null值
 * @param {Array} data - 原始数据数组
 * @returns {Array} 处理后的数据数组
 */
export const fillNullValues = (data) => {
	if (!data) return [];
	
	const filled = [...data];
	const n = filled.length;
	
	for (let i = 0; i < n; i++) {
		if (filled[i] === null || filled[i] === undefined || isNaN(filled[i])) {
			let prevValue = null;
			let nextValue = null;
			
			// 查找前一个有效值
			for (let j = i - 1; j >= 0; j--) {
				if (filled[j] !== null && filled[j] !== undefined && !isNaN(filled[j])) {
					prevValue = filled[j];
					break;
				}
			}
			
			// 查找后一个有效值
			for (let j = i + 1; j < n; j++) {
				if (filled[j] !== null && filled[j] !== undefined && !isNaN(filled[j])) {
					nextValue = filled[j];
					break;
				}
			}
			
			// 根据规则填充
			if (prevValue !== null && nextValue !== null) {
				filled[i] = (prevValue + nextValue) / 2;
			} else if (prevValue !== null) {
				filled[i] = prevValue * 0.8;
			} else if (nextValue !== null) {
				filled[i] = nextValue * 0.8;
			}
		}
	}
	
	return filled;
};

/**
 * 移动平均平滑处理
 * @param {Array} data - 原始数据数组
 * @param {number} windowSize - 平滑窗口大小，默认5
 * @returns {Array} 平滑后的数据
 */
export const smoothData = (data, windowSize = 5) => {
  if (!data || data.length === 0) return [];
  
  const filledData = fillNullValues(data);
  const result = [...filledData];
  const halfWindow = Math.floor(windowSize / 2);
  
  for (let i = 0; i < filledData.length; i++) {
    let sum = 0;
    let count = 0;
    
    // 计算窗口内的平均值
    for (let j = Math.max(0, i - halfWindow); j <= Math.min(filledData.length - 1, i + halfWindow); j++) {
      if (filledData[j] !== null && !isNaN(filledData[j])) {
        sum += filledData[j];
        count++;
      }
    }
    
    result[i] = count > 0 ? sum / count : filledData[i];
  }
  
  return result;
};

/**
 * 指数加权移动平均平滑
 * @param {Array} data - 原始数据数组
 * @param {number} alpha - 平滑系数(0-1)，默认0.3
 * @returns {Array} 平滑后的数据
 */
export const exponentialSmooth = (data, alpha = 0.3) => {
  if (!data || data.length === 0) return [];
  
  const filledData = fillNullValues(data);
  const result = [...filledData];
  
  if (filledData.length === 0) return result;
  
  result[0] = filledData[0]; // 第一个值保持不变
  
  for (let i = 1; i < filledData.length; i++) {
    if (filledData[i] !== null && !isNaN(filledData[i])) {
      result[i] = alpha * filledData[i] + (1 - alpha) * result[i - 1];
    } else {
      result[i] = result[i - 1]; // 缺失值用前一个平滑值填充
    }
  }
  
  return result;
};

/**
 * 批量数据平滑处理（替代原来的拟合）
 * @param {Object} data - 包含xData, yData, speedData的对象
 * @param {string} method - 平滑方法：'movingAverage' | 'exponential'，默认'movingAverage'
 * @param {number} param - 平滑参数（窗口大小或alpha值）
 * @returns {Object} 处理后的数据对象
 */
export const processSmoothingData = (data, method = 'movingAverage', param = 5) => {
  if (!data) return null;
  
  // 对所有数据序列进行null值填充
  const xFilled = fillNullValues(data.xData);
  const yFilled = fillNullValues(data.yData);
  const speedFilled = fillNullValues(data.speedData);
  
  let speedSmoothed;
  if (method === 'exponential') {
    speedSmoothed = exponentialSmooth(speedFilled, param);
  } else {
    speedSmoothed = smoothData(speedFilled, param);
  }
  
  return {
    ...data,
    xOriginal: xFilled,
    yOriginal: yFilled,
    speedSmoothed: speedSmoothed,
    speedOriginal: speedFilled
  };
};

// 修改默认导出
export default {
  fillNullValues,
  smoothData,
  exponentialSmooth,
  processSmoothingData
};