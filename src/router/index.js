import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/WelcomeView.vue') // 直接动态导入
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue')
  },
  {
    path: '/forgot-password',
    name: 'Change-password',
    component: () => import('@/views/ChangePasswordView.vue')
  },
  {
    path: '/main',
    name: 'Main',
    component: () => import('@/views/Main.vue'),
    // meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to) => {
  const authStore = useAuthStore()

  // 检查是否需要登录
  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      return {
        path: '/login',
        query: { redirect: to.fullPath }
      }
    }
  }
})
export default router