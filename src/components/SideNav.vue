<script setup>
import { ref, onMounted, Transition, computed } from 'vue'   
import { useAuthStore } from '@/stores/auth'
import { useHistoryStore } from '@/stores/history'
import {useRouter} from 'vue-router'
import axios from 'axios'
import logo from '@/components/Logo.vue'

const props = defineProps({
    // 活动选项卡
    activeTab: {
        type: String,
        required: true
    },
    // 侧栏是否折叠
    isCollapsed: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits([
    // 切换侧栏展开状态
    'toggle-collapse',
    // 切换选项卡
    'switch-tab',
    // 视频上传完成
    'video-uploaded',
    // 切换用户面板
    'toggle-user-panel'
])

// 上传对话框是否显示
const showUploadDialog = ref(false)
// 上传的文件
const selectedFile = ref(null)
// 上传进度
const uploadProgress = ref(0)
// 上传速度
const uploadSpeed = ref('0 MB/s');
// 上传剩余时间
const estimatedTime = ref('00:00');

let startTime = 0;
let lastLoaded = 0;

// 上传状态 null | 'uploading' | 'success' | 'cancel' | 'error'
const uploadStatus = ref(null) 
// 上传错误信息
const errorMessage = ref('')
// 文件输入元素的引用
const fileInputRef = ref(null)
// 取消令牌
const source = ref(null)

// 路由
const router = useRouter()

// 状态管理
const authStore = useAuthStore()
const historyStore = useHistoryStore()

// 分析历史是否为空
const hasHistory = computed(() => {
    return historyStore.historyItems?.length > 0
})

// tabs数据
const tabs = [
  { id: 'analysis-view', label: '分析界面'},
  { id: 'analysis-history', label: '分析历史'},
  { id: 'technical-evaluation', label: '技术问答'},
]

// 页面初始化
onMounted(() => {
    if(authStore.isLoggedIn && !authStore.userInfo)
        authStore.fetchUserInfo()
})

// 返回首页
const goHome = () => {
    router.push('/')
}

// 上传视频
const triggerFileInput = () => {
    fileInputRef.value?.click()
}

const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
    if (!allowedTypes.includes(file.type)) {
        alert('仅支持 MP4、MOV 和 AVI 格式的视频');
        event.target.value = '';
        return;
    }
    if (file.size > 1024 * 1024 * 1024) {
        alert('文件大小不能超过1G');
        event.target.value = '';
        return;
    }

    selectedFile.value = file;
    showUploadDialog.value = true;
    uploadStatus.value = null;
    uploadProgress.value = 0;
}

const handleCancelUpload = () => {
    if(uploadStatus.value === 'uploading')
        cancelUpload()
    else
        closeUploadDialog()
}

// 上传取消
const cancelUpload = () => {
    if (source.value) {
        source.value.cancel('用户取消上传');
        uploadStatus.value = 'cancelled';
        setTimeout(() => {
            closeUploadDialog();
        }, 1000);
    }
}

const performUpload = () => {
    // 开发模式模拟上传进度，在5秒内完成
    if (process.env.NODE_ENV === 'development') {
        let progress = 0;
        uploadStatus.value = 'uploading';
        const interval = setInterval(() => {
            progress += 1;
            uploadProgress.value = progress;
            
            // 计算模拟的速度和剩余时间
            const speed = (selectedFile.value.size * 0.02 / 1024 / 1024).toFixed(2); // 模拟2%的文件大小每秒
            uploadSpeed.value = `${speed} MB/s`;
            
            const remainingSeconds = Math.ceil((100 - progress) / 2);
            const minutes = Math.floor(remainingSeconds / 60);
            const seconds = remainingSeconds % 60;
            estimatedTime.value = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            if (progress >= 100) {
                clearInterval(interval);
                // 模拟上传完成
                setTimeout(() => {
                    uploadStatus.value = 'success';
                    historyStore.fetchHistory();
                    setTimeout(() => {
                        closeUploadDialog();
                        emit('video-uploaded', { id: 'test', filename: selectedFile.value.name });
                    }, 2000);
                }, 500);
            }
        }, 50);
        
        // 防止真实请求发送
        return;
    }

    const formData = new FormData();
    formData.append('video', selectedFile.value);
    // 取消令牌
    source.value = axios.CancelToken.source()

    const config = {
        headers: {
            'Authorization': `Bearer ${authStore.token}`,
            'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
            const now = Date.now()
            if(startTime === 0) startTime = now
            
            const loadedBytes = progressEvent.loaded;
            const totalBytes = progressEvent.total;

            const percentCompleted = Math.round((loadedBytes * 100) / totalBytes);
            uploadProgress.value = percentCompleted;

            const duration = (now - startTime) / 1000;
            const bytesPerSecond = (loadedBytes - lastLoaded) / duration;
            const speed = (bytesPerSecond / (1024 * 1024)).toFixed(2);
            uploadSpeed.value = `${speed} MB/s`;

            if (bytesPerSecond > 0) {
                const remainingBytes = totalBytes - loadedBytes;
                const remainingTime = remainingBytes / bytesPerSecond;
                const minutes = Math.floor(remainingTime / 60);
                const seconds = Math.floor(remainingTime % 60);
                estimatedTime.value = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
            lastLoaded = loadedBytes;
            startTime = now;
        },
        cancelToken: source.value.token
    };

    uploadStatus.value = 'uploading'

    axios.post('/api/upload', formData, config)
    .then(response => {
      uploadStatus.value = 'success'
      historyStore.fetchHistory()
      setTimeout(() => {
        closeUploadDialog()
        emit('video-uploaded', response.data)
      }, 2000)
    })
    .catch(error => {
      if(axios.isCancel(error)) {
        // 上传取消
        uploadStatus.value = 'cancelled';
        errorMessage.value = '用户取消上传';

      }else if(error.response) {
        // 服务器返回错误
        uploadStatus.value = 'error'
        if(error.response.status === 401) {
            // 认证失败，可能需要重新登录
            errorMessage.value = '认证失败,请重新登录(2秒后自动跳转)';
            setTimeout(() => {
                authStore.logout()
                router.push('/login')
            }, 2000)
        }else if(error.response.status === 413) {
            // 文件大小超过限制
            errorMessage.value = '文件大小不能超过1G,请重新选择';
        }else {
            errorMessage.value = `服务器错误: ${error.response.data.message || '上传失败'}`;
        }
      }else if (error.request) {
        // 无响应
        uploadStatus.value = 'error';
        errorMessage.value = '网络错误,请检查网络连接后重试';
      }else {
        // 请求配置错误
        uploadStatus.value = 'error';
        errorMessage.value = '上传失败,请求配置错误';
      }
    })
}

const closeUploadDialog = () => {
    showUploadDialog.value = false
    selectedFile.value = null
    uploadProgress.value = 0
    uploadStatus.value = null
    uploadSpeed.value = ''
    estimatedTime.value = ''
    if (fileInputRef.value) {
        fileInputRef.value.value = '';
    }
}

const statusInfo = computed(() => {
    if(uploadStatus.value === 'success') {
        return {
            message: '上传成功, 请耐心等待处理',
            class: 'status-success'
        }
    }else if(uploadStatus.value === 'error') {
        return {
            message: errorMessage.value,
            class: 'status-error'
        }
    }else if(uploadStatus.value === 'cancelled') {
        return {
            message: errorMessage.value,
            class: 'status-cancelled'
        }
    }   
    return null;
})

const handleTabClick = (tab) => {
    // 分析历史选项卡点击异常处理
    if (tab.id === 'analysis-history' && !hasHistory.value) {
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
            <img src="@/assets/layout_left_bar_open_icon.png" alt="打开侧栏" />
        </button>
    </transition>
    <nav class="user-sidebar" :class="{'collapsed': isCollapsed}">

        <h3 class="logo">
            <logo />
        </h3>
        <button class="collapse-btn" @click="$emit('toggle-collapse')">
            <img src="@/assets/layout_left_bar_close_icon.png" alt="关闭侧栏">
        </button>
        <div class="sidebar-header">
            <input
                type="file"
                ref="fileInputRef"
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
        
        <!-- 核心功能区域 -->
        <ul class="sidebar-nav">
            <li
                v-for="tab in tabs"
                :key="tab.id"
                :class="{'active': activeTab === tab.id,}"
                class="nav-item"
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
                        <p>文件名: {{ selectedFile?.name }}</p>
                        <p>文件类型: {{ selectedFile?.type }}</p>
                        <p>文件大小: {{ selectedFile ? (selectedFile.size / 1024 / 1024).toFixed(2) : '0' }}MB</p>
                    </div>
                    
                    <div v-if="uploadStatus === 'uploading'" class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                            <span class="progress-text">{{ uploadProgress }}%</span>
                        </div>
                        <div class="progress-info">
                            <span class="upload-speed">速度: {{ uploadSpeed }}</span>
                            <span class="estimated-time">剩余: {{ estimatedTime }}</span>
                        </div>
                    </div>

                    <div v-if="statusInfo" :class="statusInfo.class">
                        {{ statusInfo.message }}
                    </div>

                    <div class="modal-actions">
                        <button
                            v-if="!uploadStatus"
                            class="confirm-btn"
                            @click="performUpload"
                        >
                            确定上传
                        </button>
                        <!-- 上传无法中断，需要优化 -->
                        <button
                            class="cancel-btn"
                            @click="handleCancelUpload"
                        >
                            {{ uploadStatus === 'uploading' ? '中断上传' : '关闭' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
        
        <!-- 用户入口 -->
        <div
            class="user-entry"
            @click="emit('toggle-user-panel')"
        >
        <div class="user-avatar">
            <img src="@/assets/default-avatar.png" alt="用户" />
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
    /* 上传弹窗 */
    .upload-modal{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
    }

    .modal-content{
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        width: 400px;
        max-width: 90%;
    }

    .file-info {
        padding: 0.6rem 1.2rem ;
        border-radius: 12px;
        margin-bottom: 1rem;
        background-color: #eeeeee;
    }
    
    .progress-container {
        margin: 16px 0;
    }

    .progress-bar {
        height: 20px;
        background: #eee;
        border-radius: 12px;
        position: relative;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: #42b983;
        transition: width 0.3s ease;
    }

    .progress-text {
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        color: rgb(0, 0, 0);
        font-weight: bold;
    }

    .progress-info {
        display: flex;
        justify-content: space-between;
        margin-top: 8px;
        font-size: 14px;
    }

    .upload-speed,
    .estimated-time {
        color: #555;
    }

    .status-success, .status-error, .status-cancelled {
        color: #42b983;
        padding: 10px;
        text-align: center;
    }

    .status-error {
        color: #ff4757;
    }

    .status-cancelled {
        color: #f35240;
    }

    .modal-actions {
        margin-top: 1rem;
        display: flex;
        gap: 1rem;
        justify-content: flex-end;
    }

    .confirm-btn, .cancel-btn{
        background-color: #42b983;
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1rem;
        transition: background-color 0.3s ease;
    }

    .cancel-btn{
        background-color: #bdbdbd;
    }

    .confirm-btn:hover {
        background: #4bd496;
    }

    .cancel-btn:hover {
        background: #ebebeb;
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