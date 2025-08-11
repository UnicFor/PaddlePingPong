<script setup>
import { ref } from 'vue'
import AuthPanel from '@/components/UserPanel.vue';
</script>

<template>
  <body class="test-container">
    <AuthPanel />
  </body>
</template>

<style scoped>
.test-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}
</style>