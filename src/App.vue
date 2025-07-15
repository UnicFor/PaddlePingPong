<!-- App.vue -->
<template>
  <router-view></router-view>
</template>

<script setup>
  import { useAuthStore } from '@/stores/auth';
  import {onMounted} from "vue";

  const authStore = useAuthStore();

  // 在应用启动时自动获取用户信息
  onMounted(async () => {
    if (authStore.isLoggedIn) {
      await authStore.fetchUserInfo();
    }
  });
</script>

<style>
#app {
  width: 100%;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>