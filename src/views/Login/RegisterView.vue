<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import logo from "@/components/Logo.vue";

const router = useRouter()
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const smsCode = ref('')
const countdown = ref(0)

// 复用相同的短信验证码逻辑
const getSmsCode = () => {
  const phoneRegex = /^(?:(?:\+|00)86)?1[3-9]\d{9}$/
  if (!phoneRegex.test(phone.value)) {
    alert('请输入有效的手机号码')
    return
  }

  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

const handleRegister = () => {
  // 添加注册逻辑
  if (password.value !== confirmPassword.value) {
    alert('两次输入的密码不一致')
    return
  }
  router.push('/login')
}
</script>

<template>
  <div class="login-container">
    <div class="login-header">
      <h1><logo /></h1>
    </div>
    <div class="login-header">
      <h2>用户注册</h2>
    </div>

    <form @submit.prevent="handleRegister">
      <div class="form-group">
        <input
          type="tel"
          v-model="phone"
          placeholder="请输入手机号"
          required
        >
      </div>

      <div class="form-group">
        <input
          type="password"
          v-model="password"
          placeholder="设置登录密码"
          required
        >
      </div>

      <div class="form-group">
        <input
          type="password"
          v-model="confirmPassword"
          placeholder="确认登录密码"
          required
        >
      </div>

      <div class="form-group">
        <div class="sms-input">
          <input
            type="text"
            v-model="smsCode"
            placeholder="验证码"
            required
          >
          <button
            type="button"
            class="sms-btn"
            :disabled="countdown > 0"
            @click="getSmsCode"
          >
            {{ countdown ? `${countdown}s` : '获取验证码' }}
          </button>
        </div>
      </div>

      <button type="submit" class="submit-btn">立即注册</button>
    </form>

    <div class="footer-links">
      <router-link to="/login">已有账号 ? 立即登录</router-link>
    </div>
  </div>
</template>

<style scoped src="@/assets/css/login.css"></style>