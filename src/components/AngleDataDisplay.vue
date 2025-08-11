<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  angles: {
    type: Object,
    required: true
  }
})

const getStatusClass = (value, optimal, min, max) => {
  if (value >= min && value <= max) {
    return Math.abs(value - optimal) <= 10 ? 'status-good' : 'status-warning'
  }
  return 'status-bad'
}
</script>

<template>
  <div class="stat-card">
    <h3 class="stat-title">实时角度监测</h3>
    <div class="angle-grid">
      <div v-if="angles.leftElbowAngle !== undefined" class="angle-item">
        <div class="angle-meta">
          <span class="stat-label">左肘弯曲</span>
          <span class="stat-unit">基准: 90°</span>
        </div>
        <span :class="['stat-value', getStatusClass(angles.leftElbowAngle, 90, 70, 130)]">
          {{ angles.leftElbowAngle.toFixed(1) }}°
        </span>
      </div>

      <div v-if="angles.rightElbowAngle !== undefined" class="angle-item">
        <div class="angle-meta">
          <span class="stat-label">右肘弯曲</span>
          <span class="stat-unit">基准: 90°</span>
        </div>
        <span :class="['stat-value', getStatusClass(angles.rightElbowAngle, 90, 70, 130)]">
          {{ angles.rightElbowAngle.toFixed(1) }}°
        </span>
      </div>

      <div v-if="angles.torsoRotationAngle !== undefined" class="angle-item">
        <div class="angle-meta">
          <span class="stat-label">躯干扭转</span>
          <span class="stat-unit">基准: 10°</span>
        </div>
        <span :class="['stat-value', getStatusClass(angles.torsoRotationAngle, 10, 0, 30)]">
          {{ angles.torsoRotationAngle.toFixed(1) }}°
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-title {
  color: #1a365d;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 18px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 12px;
}

.angle-grid {
  display: grid;
  gap: 16px;
}

.angle-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.angle-meta {
  display: grid;
  gap: 4px;
}

.stat-label {
  color: #475569;
  font-size: 14px;
  font-weight: 500;
}

.stat-unit {
  color: #94a3b8;
  font-size: 12px;
  letter-spacing: -0.2px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  font-feature-settings: "tnum";
  letter-spacing: -0.5px;
}

.status-good { color: #16a34a; }
.status-warning { color: #ea580c; }
.status-bad { color: #dc2626; }
</style>