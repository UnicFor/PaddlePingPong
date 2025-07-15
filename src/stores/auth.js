import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 从localStorage初始化登录状态
    const isLoggedIn = ref(!!localStorage.getItem('jwt'))
    const token = ref(localStorage.getItem('jwt') || null)
    const userInfo = ref(null)

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

  // 初始化时尝试从本地存储恢复状态
  const initialize = () => {
    const savedToken = localStorage.getItem('jwt')
    if (savedToken) {
      token.value = savedToken
      isLoggedIn.value = true
    }
  }

  // 获取用户信息方法
  const fetchUserInfo = async () => {
    try {
      const response = await fetch('/api/user-info', {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      })

      if (!response.ok) {
        console.error('请求失败，状态码:', response.status);
        logout();
        return;
      }
      // 请求成功时解析数据
      const { data } = await response.json();

      const registrationDate = new Date(data.registration_date);
      const today = new Date();
      const diffTime = today - registrationDate;
      data.days = Math.floor(diffTime / (1000 * 60 * 60 * 24));

      userInfo.value = data;
    } catch (error) {
      // 捕获网络错误或其他异常
      console.error('用户信息获取失败:', error)
      logout()
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