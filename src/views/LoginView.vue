<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

import logo from "@/components/Logo.vue";

const router = useRouter()
const loginType = ref('password')
const phone = ref('')
const password = ref('')
const smsCode = ref('')
const countdown = ref(0)

const getSmsCode = async () => {
  try {
    const response = await axios.post('/api/send_sms', { phone: phone.value })
    if (response.data.success) {
      countdown.value = 60
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) clearInterval(timer)
      }, 1000)
    }
  } catch (error) {
    alert(error.response?.data.message || '发送验证码失败')
  }
}

const handleSubmit = async () => {
  try {
    const payload = {
      phone: phone.value,
      type: loginType.value
    }

    if (loginType.value === 'password') {
      payload.password = password.value
    } else {
      payload.sms_code = smsCode.value
    }

    const response = await axios.post('/api/password_login', payload)
    if (response.data.success) {
      // 保存登录状态
      const authStore = useAuthStore()
      await authStore.login(response.data.token)

      await router.push('/main')
    } else {
      alert(response.data.message)
    }
  } catch (error) {
    alert(error.response?.data.message || '登录失败')
  }
}

</script>

<template>
  <div class="login-container">
    <div class="login-header">
      <h1>
        <logo />
      </h1>
    </div>
    <div class="login-header">
      <h2>用户登录</h2>
    </div>

    <div class="login-tabs">
      <button
        class="tab"
        :class="{ active: loginType === 'password' }"
        @click="loginType = 'password'"
      >
        密码登录
      </button>
      <button
        class="tab"
        :class="{ active: loginType === 'sms' }"
        @click="loginType = 'sms'"
      >
        验证码登录
      </button>
    </div>

    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <input
          type="tel"
          v-model="phone"
          placeholder="请输入手机号"
          required
        >
      </div>

      <!-- 密码登录 -->
      <div class="form-group" v-if="loginType === 'password'">
        <input
          type="password"
          v-model="password"
          placeholder="请输入密码"
          required
        >
      </div>

      <!-- 验证码登录 -->
      <div class="form-group" v-if="loginType === 'sms'">
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

      <button type="submit" class="submit-btn">立即登录</button>
    </form>

    <div class="third-login">
      <div class="divider">或使用以下方式登录</div>
      <button class="wechat-login">
        <img src="@/assets/wechat-logo.png" alt="微信登录">
        微信扫码登录
      </button>
    </div>

    <div class="footer-links">
      <router-link to="/forgot-password">忘记密码</router-link>
      <router-link to="/register">注册账号</router-link>
    </div>
  </div>
</template>

<style scoped src="@/assets/css/login.css"></style>