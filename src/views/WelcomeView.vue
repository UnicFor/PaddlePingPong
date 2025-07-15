<script setup>
import WelcomeModel from "@/components/WelcomeModel.vue";
import Abstract from "@/components/Abstract.vue";
</script>

<template>
  <div>
    <WelcomeModel />
    <Abstract />
  </div>
</template>


<style scoped>
/* 基础移动优先样式 */
.container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
  min-height: 100vh;
}

/* 通用组件间距控制 */
.welcome-component,
.abstract-component {
  margin: 0 auto;
  width: 100%;
  max-width: 100%;
}

/* 平板及以上设备适配 */
@media (min-width: 768px) {
  .container {
    flex-direction: row;
    padding: 2rem;
    gap: 2rem;
  }

  .welcome-component {
    flex: 1.2;
    min-width: 400px;
  }

  .abstract-component {
    flex: 0.8;
    max-width: 380px;
  }
}

/* 桌面大屏优化 */
@media (min-width: 1200px) {
  .container {
    max-width: 1440px;
    margin: 0 auto;
  }
}

/* 手机端专属适配 */
@media (max-width: 480px) {
  .container {
    padding: 0.5rem;
  }

  .welcome-component {
    transform: scale(0.98); /* 小幅缩放优化布局 */
    margin-bottom: -10px;
  }
}

/* 横屏手机特殊处理 */
@media (max-width: 768px) and (orientation: landscape) {
  .container {
    flex-direction: row;
    padding: 1rem;
  }

  .abstract-component {
    max-width: 45%;
  }
}
</style>
