<template>
  <div class="server-monitor">
    <h3>服务器压力反馈</h3>
    
    <div class="placeholder-content">
      <p>服务器监控组件</p>
      <div class="data">
        <div class="item">
          <span>CPU: 45%</span>
          <div class="progress-bar">
            <div class="progress" style="width: 45%"></div>
          </div>
        </div>
        
        <div class="item">
          <span>内存: 62%</span>
          <div class="progress-bar">
            <div class="progress" style="width: 62%"></div>
          </div>
        </div>
        
        <div class="item">
          <span>延迟: 120ms</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

</script>

<style scoped>
.server-monitor {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.placeholder-content {
  text-align: center;
  color: #666;
}

.small {
  font-size: 14px;
  color: #888;
}

ul {
  text-align: left;
  font-size: 14px;
  color: #666;
  max-width: 200px;
  margin: 10px auto;
}

.data {
  margin-top: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 4px;
}

.item {
  margin-bottom: 10px;
  font-size: 14px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 5px;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #52c41a 0%, #faad14 50%, #ff4d4f 100%);
  transition: width 0.3s ease;
}
</style>