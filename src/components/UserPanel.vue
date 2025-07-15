<script>
import { useAuthStore } from '@/stores/auth'

export default {
  props: {
    show: {
      type: Boolean,
      default: false
    },
    userInfo: {
      type: Object,
      default: () => ({
        name: '未命名',
        days: 10,
        mobile: '未绑定',
        wechatBound: false,
      })
    }
  },
  emits: ['close'],
  methods: {
    handleClose() {
      this.$emit('close')
    },
    handleBind(type) {
      console.log(`绑定${type}`)
      // 实际绑定逻辑
    },
    async handleLogout() {
      if (confirm('确定要退出登录吗？退出后将清除本机登录记录')) {
        await this.$router.push('/login')
        this.authStore.logout()
        this.handleClose()
      }
    }
  },
  setup() {
    const authStore = useAuthStore()
    return { authStore }
  }
}
</script>

<template>
  <teleport to="body">
    <transition name="panel-slide">
      <div v-if="show" class="user-panel-wrapper">
        <div class="user-panel">
          <div class="panel-close" @click="handleClose">
            <svg width="14" height="14" viewBox="0 0 24 24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </div>

          <!-- 用户信息 -->
          <div class="user-header">
            <div class="avatar">
              <img src="@/assets/default-avatar.png" alt="avatar">
            </div>
            <div class="user-meta">
              <h3>{{ authStore.userInfo?.username ?? '加载中...' }}</h3>
              <p>与 Paddle PingPong 共度 {{ authStore.userInfo?.days  ?? 'n' }} 天</p>
            </div>
          </div>

          <!-- 设置列表 -->
          <div class="settings-container">
            <!-- 账号设置 -->
            <section class="settings-group">
              <h4 class="group-title">账号设置</h4>
              <div class="setting-item">
                <span>手机号</span>
                <div class="action">
                  <span class="status">{{ authStore.userInfo?.phone ? authStore.userInfo?.phone : '未绑定'}}</span>
                  <button class="bind-btn" @click="handleBind('mobile')">绑定</button>
                </div>
              </div>
              <div class="setting-item">
                <span>微信账号</span>
                <div class="action">
                  <span class="status">{{ authStore.userInfo?.weixin ? authStore.userInfo?.weixin : '未绑定' }}</span>
                  <button
                      class="bind-btn"
                      @click="handleBind('wechat')"
                  >
                    {{ authStore.userInfo?.weixin ? '解绑' : '绑定' }}
                  </button>
                </div>
              </div>
            </section>

            <!-- 帮助与反馈 -->
            <section class="settings-group">
              <h4 class="group-title">帮助与反馈</h4>
              <div class="setting-item link-item">
                <span>使用帮助</span>
                <span class="arrow">›</span>
              </div>
              <div class="setting-item link-item">
                <span>意见反馈</span>
                <span class="arrow">›</span>
              </div>
            </section>

            <!-- 关于 -->
            <section class="settings-group">
              <h4 class="group-title">关于 Paddle PingPong</h4>
              <div class="setting-item link-item">
                <span>服务协议</span>
                <span class="arrow">›</span>
              </div>
              <div class="setting-item link-item">
                <span>隐私协议</span>
                <span class="arrow">›</span>
              </div>
              <div class="setting-item link-item">
                <span>开源条款</span>
                <span class="arrow">›</span>
              </div>
            </section>

            <!-- 模型信息 -->
            <section class="settings-group">
              <h4 class="group-title">百度飞浆大模型版本</h4>
              <div class="setting-item">
                <span>当前版本</span>
                <span class="version">V0.1.4</span>
              </div>
              <div class="setting-item link-item">
                <span>模型介绍</span>
                <span class="arrow">›</span>
              </div>
            </section>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <button class="logout-btn" @click="handleLogout">退出登录</button>
              <button class="delete-account">注销账号</button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<style scoped src="@/assets/css/user-panel.css"></style>