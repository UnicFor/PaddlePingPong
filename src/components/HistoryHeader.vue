<script setup>

</script>

<template>
  <div class="virtual-header">
    <div>分析时间</div>
    <div>状态</div>
    <div>有效期</div>
    <div>操作</div>
  </div>
</template>

<style scoped>
.virtual-header {
  display: grid;
  gap: 1rem;
  grid-template-columns: 2fr 1fr 1.6fr 0.8fr;
  background: #e1e9ea;
  border-radius: 8px 8px 0 0;
  padding: 1rem 1rem 1rem 2.4rem;
  font-weight: 600;
  color: #5a6a85;
}

@media (max-width: 768px) {
  .virtual-header {
    gap: 0;
    padding: 1rem;
  }
}
</style>