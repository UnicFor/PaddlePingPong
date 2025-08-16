<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  show: {
    type: Boolean,
    default: true
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
})

const emit = defineEmits(['close'])

const router = useRouter()
const authStore = useAuthStore()

const handleClose = () => {
  emit('close')
}

const handleBind = (type) => {
  console.log(`绑定${type}`)
}

const handleLogout = async () => {
  if (confirm('确定要退出登录吗？退出后将清除本机登录记录')) {
    await router.push('/login')
    authStore.logout()
    handleClose()
  }
}
</script>

<template>
  <teleport to="body">
    <transition name="panel-slide">
      <div v-if="show" class="user-panel-wrapper">
        <div class="user-panel">
          <div class="panel-close" @click="handleClose">
            <!-- 关闭按钮 -->
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path d="M19 6.41 L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </div>

          <!-- 用户信息 -->
          <div class="user-header">
            <div class="avatar">
              <img src="@/assets/picture/default-avatar.png" alt="avatar">
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
                  <button 
                    class="bind-btn" 
                    @click="handleBind('mobile')"
                    :class="{'disabled': authStore.userInfo?.phone}"
                  >
                    {{ authStore.userInfo?.phone ? '已绑定' : '绑定' }}
                  </button>
                </div>
              </div>
              <div class="setting-item">
                <span>微信账号</span>
                <div class="action">
                  <span class="status">{{ authStore.userInfo?.weixin ? authStore.userInfo?.weixin : '未绑定' }}</span>
                  <button
                      class="bind-btn"
                      @click="handleBind('wechat')"
                      :class="{'disabled': authStore.userInfo?.phone}"
                  >
                    {{ authStore.userInfo?.weixin ? '已绑定' : '绑定' }}
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
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<style scoped>
/* 用户面板容器 */
.user-panel-wrapper {
    position: fixed;
    inset: 0 0 0 auto;
    width: 400px;
    background: #fff;
    box-shadow: -2px 0 12px rgba(0, 0, 0, 0.08);
    display: flex;
    flex-direction: column;
}

/* 用户面板内容 */
.user-panel {
    flex: 1;
    height: 100%;
    overflow-y: auto;
    padding: 24px;
}

/* 用户头部信息 */
.user-header {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

/* 头像样式 */
.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 16px;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 用户元信息 */
.user-meta h3 {
  margin: 0;
  font-size: 18px;
  color: #2c3e50;
}

.user-meta p {
  margin: 4px 0 0;
  color: #95a5a6;
  font-size: 14px;
}

/* 设置组 */
.settings-group {
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 20px;
}

/* 组标题 */
.group-title {
  color: #95a5a6;
  font-size: 14px;
  margin: 0 0 16px;
  padding-left: 12px;
}

/* 设置项 */
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 4px;
}

.setting-item span {
  font-size: 16px;
  color: #2c3e50;
}

/* 操作区域 */
.action {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 状态文本 */
.status {
  color: #95a5a6;
  font-size: 14px;
}

/* 绑定按钮 */
.bind-btn {
  padding: 6px 14px;
  background: #2d3436;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.bind-btn.disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.bind-btn:hover {
  background: #636e72;
}

/* 链接项 */
.link-item {
  background: transparent;
  padding: 12px 16px;
  border-radius: 0;
}

/* 箭头 */
.arrow {
  color: #95a5a6;
  font-size: 20px;
}

/* 版本号 */
.version {
  color: #2d3436;
  font-weight: 500;
}

/* 操作按钮区域 */
.action-buttons {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 退出登录按钮 */
.logout-btn {
  padding: 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  transition: all 0.2s ease;
  background: #f8f9fa;
  color: #2c3e50;
}

.logout-btn:hover {
  background: #e9ecef;
}

/* 动画效果 */
.panel-slide-enter-active {
  animation: panelSlideIn 0.5s cubic-bezier(0.23, 1, 0.32, 1);
}

.panel-slide-leave-active {
  animation: panelSlideIn 0.3s reverse;
}

@keyframes panelSlideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-panel-wrapper {
    width: 100%;
  }
}
</style>