<template>
  <div class="user-container">
    <SidebarNav
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

      <UserPanel
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

<script>
import { shallowRef, markRaw, defineAsyncComponent } from 'vue'
import SidebarNav from '@/components/SidebarNav.vue'
import UserPanel from '@/components/UserPanel.vue'

const AnalysisHistory = markRaw(defineAsyncComponent(() =>
  import('@/views/AnalysisHistory.vue')
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

export default {
  components: {
    SidebarNav, UserPanel
  },
  data() {
    return {
      isMobile: false,
      activeTab: 'analysis-history',
      showUserPanel: false,
      isSidebarCollapsed: false,
      componentsMap: shallowRef({
        'analysis-history': AnalysisHistory,
        'technical-evaluation': TechnicalEvaluation,
        'analysis-view':Analysis
      }),
    }
  },
  computed: {
    activeComponent() {
      return this.componentsMap[this.activeTab]
    },
    sidebarWidth() {
      return this.isMobile ? '0' : (this.isSidebarCollapsed ? '20px' : '240px')
    }
  },
  mounted() {
    this.checkIsMobile()
    window.addEventListener('resize', this.checkIsMobile)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkIsMobile)
  },
  methods: {
    switchTab(tab) {
      this.activeTab = tab
    },
    switchToAnalysisView() {
      this.activeTab = 'analysis-view'
    },
    toggleUserPanel() {
      this.showUserPanel = !this.showUserPanel
    },
    handleLogout() {
      localStorage.removeItem('mockAuth')
      localStorage.removeItem('mockUser')
      this.$router.push('/login')
    },
    checkIsMobile() {
    this.isMobile = window.innerWidth <= 768
      if (this.isMobile && !this.isSidebarCollapsed) {
        this.isSidebarCollapsed = true
      }
    }
  }
}
</script>

<style scoped>
.user-container {
  display: block;
  grid-template-columns: 240px 1fr;
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