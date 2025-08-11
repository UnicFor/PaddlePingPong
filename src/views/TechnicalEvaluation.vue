<template>
  <div class="chat-container">
    <aside class="sidebar">
      <!-- 模型选择区域 -->
      <div class="bar-section model-section">
        <h4 class="section-title">模型切换</h4>
        <div class="select-group">
          <select v-model="selectedApi" class="form-select">
            <option value="qianfan">百度千帆</option>
            <option value="openai">OpenAI</option>
          </select>
          <select v-model="selectedModel" class="form-select">
            <option
              v-for="model in apiModels[selectedApi]"
              :value="model.value"
              :key="model.value">
              {{ model.text }}
            </option>
          </select>
        </div>
      </div>

      <!-- 模式选择区域 -->
      <div class="bar-section mode-section">
        <h4 class="section-title">模式选择 RAG</h4>
        <div class="select-group">
          <label v-for="mode in modes" :key="mode.value">
            <input
              type="radio"
              v-model="selectedMode"
              :value="mode.value"
              @change="selectedMode === 'expert' && load_embedding()"
            >
            <span>{{ mode.label }}</span>
          </label>
        </div>
      </div>

      <!-- 功能操作区域 -->
      <div class="bar-section">
        <div class="select-group">
          <label>
            <input type="checkbox" v-model="graphRagEnabled">
            <span>GraphRAG</span>
          </label>
          <label class="file-upload">
            📁 上传文档
            <input
              type="file"
              @change="handleFileUpload"
              multiple
              hidden
            >
          </label>
        </div>

        <!-- 报告功能区域 -->
        <div class="report-section">
          <button
            @click="loadReport"
            class="btn report-btn">
            加载当前报告
          </button>
          <button
            @click="generateReport"
            id="generate-btn"
            class="btn report-btn">
            重新生成报告
          </button>
          <button
            @click="downloadReport"
            id="download-btn"
            class="btn report-btn"
            style="display: none;">
            下载报告
          </button>
          <button
            id="generating-btn"
            class="btn report-btn"
            style="display: none;"
            disabled>
            生成中...
          </button>
        </div>

        <button @click="clearHistory" class="btn clear-btn">清除历史</button>
      </div>
    </aside>

    <!-- 聊天主区域 -->
    <div class="chat-wrapper">
      <div class="chat-history" ref="chatHistory">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['chat-message', message.role]"
        >
          <MarkdownRenderer :content="message.content" />
        </div>
        <div v-if="isLoading" class="chat-message assistant loading-message">
          <div class="loading-indicator">
            <span>思考中</span>
            <div class="loading-dots">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <input
          v-model="inputMessage"
          @keyup.enter="sendMessage"
          class="chat-input"
          placeholder="输入你的问题..."
        >
        <button @click="sendMessage" class="btn send-btn">
          <span class="btn-content">发送</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { useAuthStore } from '@/stores/auth'
import { useHistoryStore } from '@/stores/history'

export default {
  components: {
    MarkdownRenderer
  },
  data() {
    return {
      messages: [],
      isLoading: false,
      inputMessage: '',
      report: '',
      selectedApi: 'qianfan',
      selectedModel: 'ernie-x1',
      selectedMode: 'custom',
      graphRagEnabled: true,
      apiModels: {
        openai: [
          { value: 'gpt-4o', text: 'GPT-4o' },
          { value: 'gpt-3.5-turbo', text: 'GPT-3.5' }
        ],
        qianfan: [
          { value: 'ernie-x1', text: 'ERNIE X1' },
          { value: 'ernie-4.5', text: 'ERNIE 4.5' },
          { value: 'deepseek-r1', text: 'DeepSeek R1' },
          { value: 'deepseek-v3', text: 'DeepSeek V3' }
        ]
      },
      modes: [
        { value: 'custom', label: '自定义' },
        { value: 'expert', label: '专家' }
      ]
    }
  },
  created() {
    this.authStore = useAuthStore()
    this.historyStore = useHistoryStore()
  },
  mounted() {
    this.$nextTick(() => {
      if (this.messages.length === 0) {
        this.sendWelcomeMessage()
      }
    })
  },
  computed: {
    currentVideoId() {
      const analysis = this.historyStore.historyItems.find(
        item => item.id === this.historyStore.currentAnalysisId
      )
      return analysis?.video_id || null
    }
  },
  watch: {
    selectedApi(newVal) {
      this.selectedModel = this.apiModels[newVal][0].value
    }
  },
  methods: {
    async sendMessage() {
      const content = this.inputMessage.trim().replace(/\n/g, '\n\n')
      if (!content) return

      this.messages.push({ role: 'user', content })
      this.inputMessage = ''
      this.isLoading = true

      await this.$nextTick(() => {
        this.$refs.chatHistory.scrollTop = this.$refs.chatHistory.scrollHeight
      })

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: content,
            chat_history: this.messages.slice(-5),
            mode: this.selectedMode,
            graphrag: this.graphRagEnabled,
            report: this.report,
            selected_api: this.selectedApi,
            selected_model: this.selectedModel
          })
        })

        const data = await response.json()
        let result = ''
        for await (const chunk of this.mockStream(data.content)) {
          result += chunk
          this.updateAssistantMessage(result)
        }
      } catch (error) {
        console.error('Error:', error)
        this.addMessage('assistant', '请求处理失败，请重试')
      } finally {
        this.isLoading = false
      }
    },

    sendWelcomeMessage() {
    const welcomeText = `
您好！我是小乒乓 (◍•ᴗ•◍)，您的智能助手!

**核心功能：**
✅ 提供乒乓球运动相关信息
✅ 生成专业的分析报告（Markdown/PDF）
✅ 针对运动报告做进一步解析与建议生成
✅ 提供自定义/专家两种RAG模式
✅ 支持文档上传与知识库管理

请随时提问或使用左侧功能面板开始分析！(ﾉ◕ヮ◕)ﾉ*.✧`

    // 避免重复添加欢迎消息
    if (!this.messages.some(msg => msg.content.includes(welcomeText))) {
      this.messages.push({
        role: 'assistant',
        content: welcomeText
      })
    }
  },

    updateAssistantMessage(content) {
      const lastMessage = this.messages[this.messages.length - 1]
      if (lastMessage?.role === 'assistant') {
        lastMessage.content = content
      } else {
        this.messages.push({ role: 'assistant', content })
      }
      this.$nextTick(() => {
        this.$refs.chatHistory.scrollTop = this.$refs.chatHistory.scrollHeight
      })
    },

    async handleFileUpload(event) {
      const files = Array.from(event.target.files)
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))

      try {
        const response = await fetch('/api/upload_eval', {
          method: 'POST',
          body: formData
        })
        const result = await response.json()

        if (result.status === 'success') {
          alert(`文件上传成功！知识图谱节点数：${result.total_nodes}, 边数：${result.total_edges}`)
        }
      } catch (error) {
        console.error('上传异常：', error)
        alert('文件上传失败，请检查文件格式')
      }
    },

    async load_embedding() {
      try {
        const response = await fetch('/api/load_dataset_embedding', {
          method: 'POST'
        })
        const result = await response.json()

        if (result.status === 'success') {
          console.log('知识库加载成功')
          alert('专家知识库已加载')
        }
      } catch (error) {
        console.error('加载失败：', error)
        alert('知识库加载失败')
      }
    },

    async generateReport() {
      try {
        document.getElementById('generate-btn').style.display = 'none'
        document.getElementById('download-btn').style.display = 'none'
        document.getElementById('generating-btn').style.display = 'inline-block'

        const response = await fetch('/api/generate_report', {
          method: 'POST' ,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authStore.token}`
          },
          body: JSON.stringify({
            video_id: this.currentVideoId
          })
        })
        const result = await response.json()

        if (result.report) {
          this.report = result.report
          document.getElementById('generating-btn').style.display = 'none'
          document.getElementById('download-btn').style.display = 'inline-block'
        }
      } catch (error) {
        console.error('生成报告失败：', error)
        alert('报告生成失败')
      }
    },

    downloadReport() {
      const blob = new Blob([this.report], { type: 'text/markdown;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = '专业分析报告.md'
      link.click()
    },

    async loadReport() {
      try {
        if (!this.currentVideoId) {
          throw new Error("请先选择要加载的分析记录")
        }

        const response = await fetch('/api/load_report', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authStore.token}`
          },
          body: JSON.stringify({
            video_id: this.currentVideoId
          })
        })

        const result = await response.json()

        if (result.status === 'success') {
          this.report = result.report
          // 将报告内容展示在聊天窗口
          this.messages.push({
            role: 'assistant',
            content: `**已加载分析报告**\n\n${result.report}`
          })
          // 显示下载按钮
          document.getElementById('download-btn').style.display = 'inline-block'
        } else {
          throw new Error(result.error || '报告加载失败')
        }
      } catch (error) {
        console.error('加载报告失败:', error)
        alert(error.message)
      }
    },

    clearHistory() {
      this.messages = []
      this.$nextTick(() => {
        this.sendWelcomeMessage()
        this.$refs.chatHistory.scrollTop = 0
      })
    },

    async* mockStream(data) {
      const lines = data.split('\n')
      for (const line of lines) {
        yield new Promise(resolve =>
          setTimeout(() => resolve(line + '\n'), 80)
        )
      }
    }
  }
}
</script>

<style scoped>
.chat-container {
  height: 90vh;
  display: flex;
  flex-direction: row;
  background: #f8f9fa;
  color: #2d3436;
  border-radius: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sidebar {
  display: flex;
  flex-wrap: nowrap;
  background: #ffffff;
  position: relative;
  z-index: 10;
  border-radius: 1rem;
  flex-direction: column;
  max-width: 150px;
  min-width: 150px;
  border-right: 1px solid #e0e6f0;
  overflow-y: auto;
  padding: 1rem 0.8rem;
}

.bar-section {
  flex-direction: column;
  margin-bottom: 1.5rem;
  max-width: 100%;
  display: flex;
  gap: 0.6rem;
  padding: 0.5rem;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
  font-size: 1rem;
  color: #636e72;
  white-space: nowrap;
}

.select-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.form-select {
  padding: 0.4rem 1rem;
  max-width: 120px;
  border-radius: 1rem;
  border: 1px solid #e0e6f0;
  background: #ffffff;
  color: #2d3436;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  flex: 1;
}

.form-select:hover {
  border-color: #7c8fb6;
  box-shadow: 0 1px 4px rgba(0, 153, 255, 0.1);
}

.select-group label {
  display: flex;
  min-width: 90px;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  border-radius: 1rem;
  background: #f4f6f8;
  transition: all 0.2s ease;
}

.select-group label:hover {
  background: #e3f2ff;
}

.upload-btn {
  padding: 0.5rem 1rem;
  background: #f4f6f8;
  color: #2d3436;
  border-radius: 1rem;
  transition: all 0.2s ease;
}

.upload-btn:hover {
  background: #e3f2ff;
  transform: translateY(-1px);
}

.report-section{
  align-items: center;
}

.report-btn{
  border-radius: 1rem;
  margin-top: 0.4rem;
  padding: 0.5rem 1.2rem ;
  border: 0;
  background: #f4f6f8;
  font-weight: bolder;
  color: #304257;
}

.clear-btn{
  border-radius: 1rem;
  border: 0;
  margin: 20px 20px 0 0;
  padding: 8px;
  background: #ecc7bb;
  font-weight: bolder;
  color: #930000;
}

.clear-btn:hover {
  transition: all 0.2s ease;
  transform: translateY(-1px);
}

.chat-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #ffffff;
  border-radius: 1rem 1rem 0 0;
}

.chat-message {
  margin: 0.8rem 0;
  padding: 0.8rem 1.0rem;
  border-radius: 1rem;
  max-width: 80%;
  font-size: 1rem;
  line-height: 1.5;
  animation: fadeInUp 0.3s ease-out;
}

.chat-message.user {
  background: #f4f9ff;
  margin-left: auto;
  border: 1px solid #7c8fb6;
}

.chat-message.assistant {
  background: #ffffff;
  border: 1px solid #e0e6f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.loading-message {
  opacity: 0.8;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-dots span {
  opacity: 0;
  animation: loading-dots 1.5s infinite;
}

.loading-dots span:nth-child(1) {
  animation-delay: 0s;
}
.loading-dots span:nth-child(2) {
  animation-delay: 0.5s;
}
.loading-dots span:nth-child(3) {
  animation-delay: 1s;
}

@keyframes loading-dots {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

.markdown-content {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.markdown-content p {
  margin: 0.6em 0;
}

.chat-message.user :deep(.markdown-content p) {
  margin: 0;
}

.input-area {
  display: flex;
  gap: 0.8rem;
  padding: 0.8rem;
  background: #ffffff;
  border-radius: 0 0 1rem 1rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.chat-input {
  flex: 1;
  padding: 0.8rem 1.2rem;
  border: 1px solid #e0e6f0;
  border-radius: 1rem;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.send-btn {
  padding: 0.8rem 1.5rem;
  background: #7c8fb6;
  color: white;
  border-radius: 1rem;
  border: 0;
  transition: all 0.2s ease;
}

.send-btn:hover {
  background: #7c8fb6;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 81, 144, 0.2);
}

/* 响应式设计 */
@media (max-width: 820px) {
  .chat-container {
    flex-direction: column; /* 改为垂直布局 */
    height: 95vh; /* 增加可视高度 */
  }

  .sidebar {
    max-width: 100%; /* 侧边栏全宽度 */
    min-width: auto;
    height: auto;
    border-right: none;
    border-bottom: 1px solid #e0e6f0;
    flex-direction: row; /* 横向排列侧边栏内容 */
    flex-wrap: wrap;
    padding: 0.8rem;
    border-radius: 1rem 1rem 0 0;
  }

  .bar-section {
    flex-direction: row; /* 横向排列设置区块 */
    margin-bottom: 0.5rem;
    gap: 0.4rem;
    padding: 0.3rem;
  }

  .section-title {
    display: none; /* 小屏幕隐藏区块标题 */
  }

  .form-select {
    max-width: 100px; /* 压缩选择框宽度 */
    padding: 0.3rem 0.6rem;
    font-size: 0.8rem;
  }

  .select-group label {
    min-width: auto;
    padding: 0.3rem 0.6rem;
  }

  .clear-btn {
    margin: 0.5rem auto; /* 居中清除按钮 */
    order: 99; /* 按钮移到最下方 */
    width: 90%;
  }

  /* 聊天区域高度调整 */
  .chat-wrapper {
    min-height: 70vh; /* 保证最小可视高度 */
  }
}


@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>