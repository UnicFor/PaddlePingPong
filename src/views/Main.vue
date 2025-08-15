<script setup>
import { shallowRef, ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import SideNav from '@/components/SideNav.vue'
import AuthPanel from '@/components/UserPanel.vue'
import { markRaw, defineAsyncComponent } from 'vue'

// 使用 defineAsyncComponent 和 markRaw 进行组件懒加载
const AnalysisHistory = markRaw(defineAsyncComponent(() =>
  import('@/views/AnalysisMain.vue')
))
const TechnicalEvaluation = markRaw(defineAsyncComponent(() =>
  import('@/views/TechnicalEvaluation.vue')
))
const Analysis = markRaw(
  defineAsyncComponent({
    loader: () => import('@/views/Analysis.vue'),
    delay: 200,
  })
)

const isMobile = ref(false)
const activeTab = ref('analysis-main')
const showUserPanel = ref(false)
const isSidebarCollapsed = ref(false)
const componentsMap = shallowRef({
  'analysis-main': AnalysisHistory,
  'analysis-view': Analysis,
  'technical-evaluation': TechnicalEvaluation,
})

const router = useRouter()

const currentUser = ref(JSON.parse(localStorage.getItem('mockUser') || 'null'))

const activeComponent = computed(() => componentsMap.value[activeTab.value])
const sidebarWidth = computed(() =>
  isMobile.value ? '0' : (isSidebarCollapsed.value ? '20px' : '240px')
)

onMounted(() => {
  checkIsMobile()
  window.addEventListener('resize', checkIsMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkIsMobile)
})

function switchTab(tab) {
  activeTab.value = tab
}

function switchToAnalysisView() {
  activeTab.value = 'analysis-view'
}

function toggleUserPanel() {
  showUserPanel.value = !showUserPanel.value
}

function handleLogout() {
  localStorage.removeItem('mockAuth')
  localStorage.removeItem('mockUser')
  router.push('/login')
}

function checkIsMobile() {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value && !isSidebarCollapsed.value) {
    isSidebarCollapsed.value = true
  }
}
</script>

<template>
  <div class="user-container">
    <SideNav
      :active-tab="activeTab"
      :is-collapsed="isSidebarCollapsed"
      @switch-tab="switchTab"
      @toggle-user-panel="toggleUserPanel"
      @toggle-collapse="isSidebarCollapsed = !isSidebarCollapsed"
    />

    <main class="user-main" :style="{ marginLeft: sidebarWidth }">
      <transition name="fade-slide" mode="out-in">
        <component
            :is="activeComponent"
            @check="switchToAnalysisView"
        />
      </transition>

      <AuthPanel
        :show="showUserPanel"
        :user-info="currentUser"
        @close="toggleUserPanel"
        @logout="handleLogout"
      />
    </main>

    <div
      v-show="isMobile && !isSidebarCollapsed"
      class="sidebar-mask"
      @click="isSidebarCollapsed = true"
    ></div>
  </div>
</template>

<style scoped>
.user-container {
  display: block;
  min-height: 100vh;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  background: #f8f9fa;
}

.user-main {
  margin-left: 260px;
  padding: 2rem;
  min-height: 80vh;
  transition: margin-left 0.3s ease;
}

.sidebar-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999;
  transition: opacity 0.3s;
}

@media (max-width: 768px) {
  .user-main {
    margin-left: 0 !important;
    padding: 2rem 10px;
  }
}
</style>