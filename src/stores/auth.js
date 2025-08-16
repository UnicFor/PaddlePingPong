import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useAuthStore = defineStore('auth', () => {
    // 统一使用 'jwt' 作为token键名
    const isLoggedIn = ref(process.env.NODE_ENV === 'development' || !!localStorage.getItem('jwt'))
    const token = ref(process.env.NODE_ENV === 'development' ? 'dev_token' : localStorage.getItem('jwt') || null)
    const userInfo = ref(process.env.NODE_ENV === 'development' ? { name: '开发用户', id: 'dev_user' } : null)

    // 登录方法
    const login = async (jwt) => {
      if (typeof jwt !== 'string' || jwt.split('.').length !== 3) {
      console.error('无效的令牌格式');
      logout();
      return;
    }

    isLoggedIn.value = true;
    token.value = jwt;
    localStorage.setItem('jwt', jwt);

    // 添加请求头验证
    try {
      await fetchUserInfo();
    } catch (error) {
      console.error('登录后验证失败:', error);
      logout();
    }
  }

  // 登出方法
  const logout = () => {
    isLoggedIn.value = false
    token.value = null
    localStorage.removeItem('jwt')
    userInfo.value = null
  }

  // 获取用户信息方法
  const fetchUserInfo = async () => {
    try {
      const response = await request.get('/api/user-info')
      const { data } = response.data
      
      const registrationDate = new Date(data.registration_date)
      const today = new Date()
      const diffTime = today - registrationDate
      data.days = Math.floor(diffTime / (1000 * 60 * 60 * 24))

      userInfo.value = data
    } catch (error) {
      console.error('用户信息获取失败:', error)
      logout()
    }
  }

  // 初始化时尝试从本地存储恢复状态
  const initialize = () => {
    if (import.meta.env.DEV) {
      const savedToken = localStorage.getItem('jwt')
      if (savedToken) {
        token.value = savedToken
        isLoggedIn.value = true
      }
    }
  }

  initialize()

  return {
    isLoggedIn,
    token,
    login,
    logout,
    userInfo,
    fetchUserInfo
  }
})