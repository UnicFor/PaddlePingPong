<script setup>
import { ref } from 'vue'
import SideNav from '@/components/SideNav.vue'
</script>

<template>
  <body class="test-container">
    <SideNav />
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