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
 * 高斯消元法解线性方程组
 * @param {Array} matrix - 系数矩阵
 * @param {Array} rhs - 右侧向量
 * @returns {Array} 解向量
 */
export const gaussianElimination = (matrix, rhs) => {
	const n = matrix.length;
	const augmented = matrix.map((row, i) => [...row, rhs[i]]);
	
	// 前向消元
	for (let i = 0; i < n; i++) {
		// 部分选主元：寻找当前列绝对值最大的行
		let maxRow = i;
		for (let k = i + 1; k < n; k++) {
			if (Math.abs(augmented[k][i]) > Math.abs(augmented[maxRow][i])) {
				maxRow = k;
			}
		}
		
		// 交换当前行与主元行
		[augmented[i], augmented[maxRow]] = [augmented[maxRow], augmented[i]];
		
		// 消去下方行的当前列元素
		for (let k = i + 1; k < n; k++) {
			const factor = augmented[k][i] / augmented[i][i];
			for (let j = i; j <= n; j++) {
				augmented[k][j] -= factor * augmented[i][j];
			}
		}
	}
	
	// 回代求解
	const solution = new Array(n);
	for (let i = n - 1; i >= 0; i--) {
		solution[i] = augmented[i][n];
		for (let j = i + 1; j < n; j++) {
			solution[i] -= augmented[i][j] * solution[j];
		}
		solution[i] /= augmented[i][i];
	}
	
	return solution;
};

/**
 * 多项式曲线拟合
 * @param {Array} xData - x轴数据
 * @param {Array} yData - y轴数据
 * @param {number} degree - 多项式阶数，默认5
 * @returns {Array} 拟合后的数据
 */
export const polynomialFit = (xData, yData, degree = 5) => {
	if (!xData || !yData || xData.length < degree + 1) return yData;
	
	// 确保yData中没有null值
	const cleanYData = fillNullValues(yData);
	const n = xData.length;
	const x = xData.map((_, i) => i); // 使用帧索引作为x值
	
	// 构建正规方程矩阵 (A^T * A) * coefficients = A^T * y
	const matrix = [];
	const rhs = [];
	
	// 计算矩阵元素：sum(x^(i+j)) 和 sum(x^i * y)
	for (let k = 0; k <= degree; k++) {
		const row = [];
		for (let j = 0; j <= degree; j++) {
			let sum = 0;
			for (let i = 0; i < n; i++) {
				sum += Math.pow(x[i], k + j);
			}
			row.push(sum);
		}
		matrix.push(row);
		
		let sum = 0;
		for (let i = 0; i < n; i++) {
			sum += cleanYData[i] * Math.pow(x[i], k);
		}
		rhs.push(sum);
	}
	
	// 使用高斯消元法解线性方程组
	const coefficients = gaussianElimination(matrix, rhs);
	
	// 生成拟合数据：计算每个x值对应的多项式值
	return x.map(xi => {
		let y = 0;
		for (let i = 0; i <= degree; i++) {
			y += coefficients[i] * Math.pow(xi, i);
		}
		return y;
	});
};

/**
 * 批量数据拟合处理
 * @param {Object} data - 包含xData, yData, speedData, frameData的对象
 * @param {number} fitDegree - 拟合阶数
 * @returns {Object} 处理后的数据对象
 */
export const processFittingData = (data, fitDegree = 4) => {
	if (!data) return null;
	
	// 对所有数据序列进行null值填充
	const xFilled = fillNullValues(data.xData);
	const yFilled = fillNullValues(data.yData);
	const speedFilled = fillNullValues(data.speedData);
	
	// 限制拟合阶数在合理范围内
	const degree = Math.min(Math.max(fitDegree, 2), 6);
	
	return {
		...data,
		xOriginal: xFilled,
		yOriginal: yFilled,
		speedFitted: polynomialFit(data.frameData, speedFilled, degree),
		speedOriginal: speedFilled
	};
};

// 默认导出所有工具函数
export default {
	fillNullValues,
	gaussianElimination,
	polynomialFit,
	processFittingData
};