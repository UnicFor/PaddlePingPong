<template>
  <div class="chat-container">
    <!-- 顶部导航栏 -->
    <aside class="sidebar">
      <div class="bar-section model-section">
        <h4 class="section-title">模型切换</h4>
        <div class="select-group">
          <select v-model="selectedApi" class="form-select">
            <option value="openai">OpenAI</option>
            <option value="volcengine">DeepSeek</option>
          </select>
          <select v-model="selectedModel" class="form-select">
            <option v-for="model in apiModels[selectedApi]"
                    :value="model.value"
                    :key="model.value">
              {{ model.text }}
            </option>
          </select>
        </div>
      </div>

      <div class="bar-section mode-section">
        <h4 class="section-title">模式选择 RAG</h4>
        <div class="select-group">
          <label v-for="mode in modes" :key="mode.value">
            <input
              type="radio"
              v-model="selectedMode"
              :value="mode.value"
              @change="toggleModeOptions"
            >
            <span>{{ mode.label }}</span>
          </label>
        </div>
        <select v-model="selectedExpert"
                v-show="selectedMode === 'expert'"
                class="form-select expert-select">
          <option value="Cybersecurity-RAG">网络安全</option>
          <option value="Medical-RAG">医疗健康</option>
        </select>
      </div>

      <div class="bar-section">
        <div v-show="selectedMode === 'custom'" class="select-group">
          <label>
            <input type="checkbox" v-model="graphRagEnabled">
            <span>RAG</span>
          </label>
          <label>
            <input type="checkbox" v-model="graphRagEnabled">
            <span>HyDE</span>
          </label>
          <label>
            <input type="checkbox" v-model="graphRagEnabled">
            <span>Reranking</span>
          </label>
          <label>
            <input type="checkbox" v-model="graphRagEnabled">
            <span>GraphRAG</span>
          </label>
          <label>
            📁 上传文档
            <input type="file" @change="handleFileUpload" multiple hidden>
          </label>
        </div>
      </div>

      <button @click="clearHistory" class="btn clear-btn">清除历史</button>
    </aside>

    <!-- 聊天区域 -->
    <div class="chat-wrapper">
      <div class="chat-history" ref="chatHistory">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['chat-message', message.role]"
        >
          {{ message.content }}
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
export default {
  data() {
    return {
      messages: [],
      inputMessage: '',
      selectedApi: 'openai',
      selectedModel: 'gpt-4o',
      selectedMode: 'custom',
      selectedExpert: 'Cybersecurity-RAG',
      graphRagEnabled: true,
      apiModels: {
        openai: [
          { value: 'gpt-4o', text: 'gpt-4o' },
          { value: 'gpt-3.5-turbo', text: 'gpt-3.5-turbo' }
        ],
        volcengine: [
          { value: 'deepseek-r1', text: 'deep-r1' },
          { value: 'deepseek-v3', text: 'deep-v3' },
        ]
      },
      modes: [
        { value: 'custom', label: '自定义' },
        { value: 'expert', label: '专家' }
      ]
    }
  },
  methods: {
    async sendMessage() {
      const prompt = this.inputMessage.trim()
      if (!prompt) return

      this.messages.push({ role: 'user', content: prompt })
      this.inputMessage = ''

      try {
        const response = await this.streamChatResponse({
          prompt,
          chatHistory: this.messages.slice(-5),
          mode: this.selectedMode,
          graphrag: this.graphRagEnabled,
          context: this.generateContext()
        })

        // 模拟流式响应
        let result = ''
        for await (const chunk of this.mockStream(response)) {
          result += chunk
          this.updateAssistantMessage(result)
        }
      } catch (error) {
        console.error('Error:', error)
        this.addMessage('assistant', '抱歉，请求处理失败')
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
    handleFileUpload(event) {
      const files = Array.from(event.target.files)
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))

      // 这里调用上传API
      console.log('Uploading files:', files)
    },
    clearHistory() {
      this.messages = []
    },
    toggleModeOptions() {
      // 模式切换时的额外处理
    },
    generateContext() {
      return this.selectedMode === 'expert'
        ? '[专家文档内容示例]'
        : '[自定义文档内容示例]'
    },
    async* mockStream(data) {
      const chunks = data.split(' ')
      for (const chunk of chunks) {
        yield new Promise(resolve =>
          setTimeout(() => resolve(chunk + ' '), 50)
        )
      }
    }
  }
}
</script>

<style scoped src="@/assets/css/technical.css"></style>
