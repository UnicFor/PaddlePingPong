<script setup>
import AnalysisHistory from '@/components/Analysis/AnalysisHistory.vue'
import ServerMonitor from '@/components/Base/ServerMonitor.vue'
import CacheMonitor from '@/components/Base/CacheMonitor.vue'
</script>

<template>
  <div class="analysis-main">
    <!-- 顶部三分栏 -->
    <div class="top-panels">
      <div class="panel-item">
        <ServerMonitor />
      </div>
      
      <div class="panel-item">
        <CacheMonitor />
      </div>
      
      <div class="panel-item">

      </div>
    </div>
    
    <AnalysisHistory />
  </div>
</template>

<style scoped>
.analysis-main {
  padding: 20px;
  min-height: 100vh;
}

.top-panels {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.panel-item {
  min-height: 300px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .top-panels {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .panel-item {
    min-height: auto;
  }
}

@media (max-width: 768px) {
  .analysis-main {
    padding: 10px;
  }
}
</style>