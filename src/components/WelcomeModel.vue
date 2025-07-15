<script setup>
import logo from "@/components/Logo.vue";
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const navigationMap = {
  login: '/login',
  analysis:'/main'
}

const handleNavigation = (type) => {
  if (type === 'analysis') {
    // 检查登录状态
    if (authStore.isLoggedIn) {
      router.push('/main')
    } else {
      router.push('/main')
      // router.push('/login?redirect=/main')
    }
  } else {
    router.push(navigationMap[type])
  }
}
</script>

<template>
  <div class="welcome-container">
    <!-- 内容容器 -->
    <div class="content-wrapper">
      <!-- 主标题 -->
      <h1 class="main-title">
        <logo />
      </h1>

      <!-- 副标题 -->
      <p class="subtitle">智能乒乓球运动分析与可视化系统</p>

      <!-- 操作按钮组 -->
      <div class="action-buttons">
        <button
            class="btn login-btn"
            @click="handleNavigation('analysis')"
        >
          <span class="btn-content">开始分析</span>
        </button>
        <button
            class="btn register-btn"
            @click="handleNavigation('login')"
        >
          <span class="btn-content">登录 / 注册</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped src="@/assets/css/welcome.css"></style>