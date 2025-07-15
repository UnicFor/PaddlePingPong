<script>
import { computed, onMounted } from 'vue'
import logo from '@/components/Logo.vue'
import { useAuthStore } from '@/stores/auth'
import { useHistoryStore } from '@/stores/history'
import axios from 'axios'

export default {
  components: { logo },
  props: {
    activeTab: {
      type: String,
      required: true
    },
    isCollapsed: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      showUploadDialog: false,
      selectedFile: null,
      uploadProgress: 0,
      uploadStatus: null, // null | 'uploading' | 'success' | 'error'
      tabs: [
        { id: 'analysis-view', label: '分析界面'},
        { id: 'analysis-history', label: '分析历史'},
        { id: 'technical-evaluation', label: '技术问答'},
      ]
    }
  },
  methods: {
    goHome() {
      this.$router.push('/')
    },
    triggerFileInput() {
      this.$refs.fileInput.click()
    },
    handleFileSelect(event){
      const file = event.target.files[0];
      if (!file) return;

      const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
      if (!allowedTypes.includes(file.type)) {
        alert('仅支持 MP4、MOV 和 AVI 格式的视频');
        return;
      }
      if (file.size > 1024 * 1024 * 1024) {
        alert('文件大小不能超过1G');
        return;
      }

      this.selectedFile = file;
      this.showUploadDialog = true;
      this.uploadStatus = null;
      this.uploadProgress = 0;
    },
    performUpload() {
      const formData = new FormData();
      formData.append('video', this.selectedFile);

      const config = {
        headers: {
          'Authorization': `Bearer ${this.authStore.token}`
        },
      };

      this.uploadStatus = 'uploading';

      axios.post('/api/upload', formData, config)
      .then(response => {
        this.uploadStatus = 'success';
        this.historyStore.fetchHistory();
        setTimeout(() => {
          this.closeUploadDialog();
          this.$emit('video-uploaded', response.data);
        }, 1500);
      })
      .catch(error => {
        this.uploadStatus = 'error';
        console.error('上传失败:', error);
      });
    },
    closeUploadDialog() {
      this.showUploadDialog = false;
      this.selectedFile = null;
      this.uploadProgress = 0;
      this.uploadStatus = null;
    },
    handleTabClick(tab) {
      if (tab.id === 'analysis-view' && !this.hasHistory) return
      this.$emit('switch-tab', tab.id)
    },
  },
  setup() {
    const authStore = useAuthStore()
    const historyStore = useHistoryStore()

    onMounted(() => {
      if (authStore.isLoggedIn && !authStore.userInfo) {
        authStore.fetchUserInfo()
      }
    })

    const hasHistory = computed(() => {
      return historyStore.historyItems?.length > 0
    })

    return {
      authStore,
      historyStore,
      hasHistory
    }
  },
}
</script>

<template>
  <transition name="button-fade">
    <button
        v-if="isCollapsed"
        class="expand-btn"
        @click="$emit('toggle-collapse')"
    >
      <img src="@/assets/layout_left_bar_open_icon.png" alt="打开侧栏" />
    </button>
  </transition>
  <nav
    class="user-sidebar"
    :class="{ collapsed: isCollapsed }"
  >
    <h3 class="logo">
      <logo />
    </h3>
    <button class="collapse-btn" @click="$emit('toggle-collapse')">
      <img src="@/assets/layout_left_bar_close_icon.png" alt="收起侧栏" />
    </button>
    <div class="sidebar-header">
      <div class="control-buttons">
          <input
        type="file"
        ref="fileInput"
        hidden
        accept="video/mp4,video/quicktime,video/x-msvideo"
        @change="handleFileSelect"
      >
        <button class="nav-item" @click="triggerFileInput">
          <span>上传视频</span>
        </button>
        <button class="nav-item" @click="goHome">
          <span>返回首页</span>
        </button>
      </div>
      <hr>
    </div>

    <ul class="sidebar-nav">
      <li
        v-for="tab in tabs"
        :key="tab.id"
        class="nav-item"
        :class="{
          active: activeTab === tab.id,
          'disabled': tab.id === 'analysis-view' && !hasHistory
        }"
        @click="handleTabClick(tab)"
      >
        <span>{{ tab.label }}</span>
      </li>
    </ul>

    <!-- 上传弹窗 -->
    <Teleport to="body">
      <div v-if="showUploadDialog" class="upload-modal">
        <div class="modal-content">
          <h3>确认上传视频</h3>

          <div class="file-info">
            <p>文件名: {{ selectedFile.name }}</p>
            <p>文件类型: {{ selectedFile.type }}</p>
            <p>文件大小: {{ (selectedFile.size / 1024 / 1024).toFixed(2) }}MB</p>
          </div>

          <!-- 上传进度条 -->
          <div v-if="uploadStatus === 'uploading'" class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: uploadProgress + '%' }"
            ></div>
            <span class="progress-text">{{ uploadProgress }}%</span>
          </div>

          <!-- 状态提示 -->
          <div v-if="uploadStatus === 'success'" class="status-success">
            上传成功
          </div>
          <div v-if="uploadStatus === 'error'" class="status-error">
            上传失败，请重试
          </div>

          <!-- 操作按钮 -->
          <div class="modal-actions">
            <button
              v-if="!uploadStatus"
              class="confirm-btn"
              @click="performUpload"
            >
              确认上传
            </button>
            <button
              class="cancel-btn"
              @click="closeUploadDialog"
              :disabled="uploadStatus === 'uploading'"
            >
              {{ uploadStatus === 'uploading' ? '上传中...' : '取消' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>



    <!-- 用户入口 -->
    <div
      class="user-entry"
      @click="$emit('toggle-user-panel')">
      <div class="user-avatar">
        <img src="@/assets/default-avatar.png" alt="用户" />
      </div>
      <span class="username">{{ authStore.userInfo?.username ?? '加载中...' }}</span>
    </div>
  </nav>
</template>

<style scoped src="@/assets/css/navbar.css"></style>
<style scoped src="@/assets/css/pop-window.css"></style>