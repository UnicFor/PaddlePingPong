<script setup>
import { onMounted, Transition, computed, ref } from 'vue'   
import { useAuthStore } from '@/stores/auth'
import { useHistoryStore } from '@/stores/history'
import { useRouter } from 'vue-router'
import UploadPanel from '@/components/Base/UploadPanel.vue'
import logo from '@/components/Base/Logo.vue'
import { useUploadStore } from '@/stores/upload.js'

const props = defineProps({
    activeTab: {
        type: String,
        required: true
    },
    isCollapsed: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits([
    'toggle-collapse',
    'switch-tab',
    'video-uploaded',
    'toggle-user-panel'
])

// 上传相关状态
const showUploadPanel = ref(false)
const selectedFile = ref(null)
const fileInputRef = ref(null)

// 路由和状态管理
const router = useRouter()
const authStore = useAuthStore()
const historyStore = useHistoryStore()
const uploadStore = useUploadStore()

const hasHistory = computed(() => {
    return historyStore.historyItems?.length > 0
})

const tabs = [
    { id: 'analysis-main', label: '功能首页'},
    { id: 'analysis-view', label: '分析界面'},
    { id: 'technical-evaluation', label: '技术问答'},
]

// 监听上传状态变化
const isUploading = computed(() => uploadStore.isUploading)
const uploadProgress = computed(() => uploadStore.progress)

// 页面初始化
onMounted(() => {
    if(authStore.isLoggedIn && !authStore.userInfo)
        authStore.fetchUserInfo()
})

// 返回首页
const goHome = () => {
    router.push('/')
}

// 处理文件选择
const handleFileSelect = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo']
    if (!allowedTypes.includes(file.type)) {
        alert('仅支持 MP4、MOV 和 AVI 格式的视频')
        event.target.value = ''
        return
    }
    
    if (file.size > 1024 * 1024 * 1024) {
        alert('文件大小不能超过1G')
        event.target.value = ''
        return
    }

    selectedFile.value = file
    showUploadPanel.value = true
}

// 触发文件选择
const triggerFileInput = () => {
    fileInputRef.value?.click()
}

// 处理上传按钮点击
const handleUploadButtonClick = async () => {
    if (isUploading.value) {
        // 如果正在上传，重新打开面板查看进度
        showUploadPanel.value = true
        return
    }
    
    // 检查是否可以上传
    try {
        await uploadStore.checkServerConnection()
        if (!uploadStore.canUpload) {
            alert(uploadStore.serverStatus === 'disconnected'
                ? '无法连接到服务器，请检查网络连接' 
                : '当前无法上传文件')
            return
        }
    } catch (error) {
        alert('服务器连接检查失败')
        return
    }
    
    // 触发文件选择
    triggerFileInput()
}

// 处理上传完成
const handleUploadComplete = (result) => {
    emit('video-uploaded', result)
    showUploadPanel.value = false
    selectedFile.value = null
    
    // 重置文件输入
    if (fileInputRef.value) {
        fileInputRef.value.value = ''
    }
}

// 处理上传错误
const handleUploadError = (error) => {
    console.error('Upload error:', error)
}

// 处理上传面板关闭
const handleUploadPanelClose = () => {
    showUploadPanel.value = false
    // 如果上传完成，清除文件
    if (!isUploading.value) {
        selectedFile.value = null
        if (fileInputRef.value) {
            fileInputRef.value.value = ''
        }
    }
}

// 处理标签页点击
const handleTabClick = (tab) => {
    if (tab.id === 'analysis-main' && !hasHistory.value) {
        alert('暂无分析历史')
        return
    }
    if (tab.id === 'analysis-view' && !hasHistory.value) return
    emit('switch-tab', tab.id)
}
</script>

<template>
    <transition name="button-fade">
        <button
            v-if="isCollapsed"
            class="expand-btn"
            @click="$emit('toggle-collapse')"
        >
            <img src="@/assets/picture/layout_left_bar_open_icon.png" alt="打开侧栏" />
        </button>
    </transition>
    
    <nav class="user-sidebar" :class="{'collapsed': isCollapsed}">
        <h3 class="logo">
            <logo />
        </h3>
        
        <button class="collapse-btn" @click="$emit('toggle-collapse')">
            <img src="@/assets/picture/layout_left_bar_close_icon.png" alt="关闭侧栏">
        </button>
        
        <div class="sidebar-header">
            <input
                type="file"
                ref="fileInputRef"
                hidden
                accept="video/mp4,video/quicktime,video/x-msvideo"
                @change="handleFileSelect"
            >
            <button 
                class="nav-item upload-btn" 
                @click="handleUploadButtonClick"
                :class="{ 'uploading': isUploading }"
            >
                <span v-if="!isUploading">上传视频</span>
                <span v-else>上传中 {{ uploadProgress }}%</span>
                <div v-if="isUploading" class="upload-spinner"></div>
            </button>
            <button class="nav-item" @click="goHome">
                <span>返回首页</span>
            </button>
        </div>
        
        <hr>
        
        <!-- 核心功能区域 -->
        <ul class="sidebar-nav">
            <li
                v-for="tab in tabs"
                :key="tab.id"
                :class="{'active': activeTab === tab.id}"
                class="nav-item"
                @click="handleTabClick(tab)"
            >
                <span>{{ tab.label }}</span>
            </li>
        </ul>

        <!-- 上传面板组件 -->
        <UploadPanel
            v-if="showUploadPanel"
            :visible="showUploadPanel"
            :file="selectedFile"
            title="上传视频"
            @close="handleUploadPanelClose"
            @uploaded="handleUploadComplete"
            @error="handleUploadError"
        />
        
        <!-- 用户入口 -->
        <div
            class="user-entry"
            @click="emit('toggle-user-panel')"
        >
            <div class="user-avatar">
                <img src="@/assets/picture/default-avatar.png" alt="用户" />
            </div>
            <span class="username">{{ authStore.userInfo?.username ?? '加载中...' }}</span>
        </div>
    </nav>
</template>

<style scoped>
    .user-sidebar {
        position: fixed;
        width: 220px;
        height: 100%;
        top: 0;
        left: 0;
        padding: 2rem 1rem;
        background-color: white;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
        z-index: 9999;
        /* 初始状态下展开 */
        transform: translateX(0);
        transition: transform 0.3s ease;
    }

    .user-sidebar.collapsed {
        transform: translateX(-100%);
    }

    .button-fade-enter-active,
    .button-fade-leave-active {
        transition: all 1s ease-in-out;
    }

    .button-fade-enter-from,
    .button-fade-leave-to {
        opacity: 0;
        transform: translateX(-20px);
    }

    .logo{
        padding: 0 1rem 1rem 1rem;
    }

    .expand-btn,
    .collapse-btn {
        position: fixed;
        padding: 0.2rem;
        left: 20px;
        top: 20px;
        background-color: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        border: none;
        border-radius: 8px;
        display: flex;
        cursor: pointer;
    }

    .expand-btn img,
    .collapse-btn img{
        height: 24px;
    }

    .collapse-btn{
        left: 200px;
    }

    .sidebar-header{
        display: flex;
        flex-direction: column;
        margin-top: 1rem;
        padding: 0 1rem;
    }

    .sidebar-header button{
        border: none;
        font-size: 1rem;
        padding: 0.5rem 1rem;
        background: white;
    }

    .sidebar-nav {
        padding: 0 1rem;
        margin-top: 1rem;
    }
    
    .nav-item {
        display: flex;
        padding: 1rem;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #636e72;
    }

    .nav-item:hover {
        background-color: #f0f0f0;
        color: #333;
    }

    .nav-item.active {
        background: #f1f3f5;
        color: #2c3e50;
        font-weight: 500;
    }

    .nav-item:hover:not(.active) {
        background-color: #e9ecef;
    }

    .nav-item span {
        font-size: 1.2rem;
    }

    .nav-item.uploading {
        background-color: #e8f5e8;
        color: #42b983;
        font-weight: bold;
        position: relative;
    }

    .upload-spinner {
        position: absolute;
        right: 16px;
        top: 12px;
        width: 16px;
        height: 16px;
        border: 2px solid #42b983;
        border-top: 2px solid transparent;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* 用户入口 */
    .user-entry{
        position: absolute;
        left: 20px;
        bottom: 100px;
        display: flex;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        padding: 12px 20px;
        border-radius: 50px;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .user-entry:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
    }

    .user-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        overflow: hidden;
    }

    .user-avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
</style>