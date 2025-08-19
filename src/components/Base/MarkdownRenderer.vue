<script setup>
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { computed, onUnmounted } from 'vue'

const props = defineProps({
  content: {
    type: String,
    required: true
  },
  // 只缓存报告
  cacheKey: {
    type: String,
    default: null
  }
})

// 组件级缓存，存储已渲染的 Markdown
const markdownCache = new Map()
const MAX_CACHE_SIZE = 10 // 限制最大缓存

// LRU 缓存实现
const getCachedMD = (key) => {
  if(!markdownCache.has(key)) 
    return null
  
  //(LRU策略)
  const value = markdownCache.get(key)
  markdownCache.delete(key)
  markdownCache.set(key, value)
  console.log('成功加载缓存')
  return value
}

const setCachedMD = (key, content) => {
  if(markdownCache.has(key)) 
    markdownCache.delete(key)

  else if(markdownCache.size >= MAX_CACHE_SIZE){
    const firstKey = markdownCache.keys().next().value
    markdownCache.delete(firstKey)
  }

  console.log('成功缓存内容')
  markdownCache.set(key, content)
}

const compiledMarkdown = computed(() => {
  if (!props.content?.trim()) return ''
  
  if(props.cacheKey) {
    const cached = getCachedMD(props.cacheKey)
    if(cached)
      return cached
  }
    
  const preprocessed = props.content
    .replace(/^(#{1,6}) /gm, '$1 ')
    .replace(/\*\*(.*?)\*\*/g, '**$1**')
    .replace(/\*(.*?)\*/g, '*$1*')
    .replace(/\[(.*?)\]\((.*?)\)/g, '[$1]($2)')
    .replace(/!\[(.*?)\]\((.*?)\)/g, '![$1]($2)')

  const rendered = DOMPurify.sanitize(
    marked.parse(preprocessed, {
      breaks: true,
      gfm: true
    }),
    {
      USE_PROFILES: { html: true },
      ADD_ATTR: ['target', 'rel'],
      // DOMPurify 默认白名单片段
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img',
                    'table', 'thead', 'tbody', 'tr', 'td', 'th']
    }
  )

  if(props.cacheKey) 
    setCachedMD(props.cacheKey, rendered)
  
  return rendered
})

// 组件卸载时清理缓存
onUnmounted(() => {
  markdownCache.clear()
})
</script>

<template>
  <div class="markdown-content" v-html="compiledMarkdown"></div>
</template>

<style scoped>
/* CSS 变量定义主题 */
.markdown-content {
  /* 亮色主题变量 */
  --text-primary: #131c24;
  --text-secondary: #202d39;
  --bg-code: #f8f9fa;
  --border-color: #e0e6f0;
  --accent-color: #4a90e2;
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
  
  /* 响应式字体大小 */
  --font-size-base: clamp(14px, 2vw, 16px);
  --font-size-small: clamp(12px, 1.5vw, 14px);
  --font-size-large: clamp(18px, 3vw, 24px);
  
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: 1.7;
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 响应式标题样式 */
.markdown-content :deep(h1) {
  font-size: clamp(1.5rem, 4vw, 2.2rem);
  margin: 1.5em 0 0.8em;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 0.3em;
  font-weight: 700;
  line-height: 1.3;
}

.markdown-content :deep(h2) {
  font-size: clamp(1.25rem, 3vw, 1.8rem);
  margin: 1.3em 0 0.7em;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.2em;
  font-weight: 600;
}

.markdown-content :deep(h3) {
  font-size: clamp(1.1rem, 2.5vw, 1.5rem);
  margin: 1.1em 0 0.6em;
  color: var(--text-secondary);
  font-weight: 600;
}

/* 响应式代码块 */
.markdown-content :deep(pre) {
  background: var(--bg-code);
  padding: clamp(0.8rem, 2vw, 1.2rem);
  border-radius: 8px;
  overflow-x: auto;
  margin: 1.2em 0;
  line-height: 1.5;
  border-left: 3px solid var(--accent-color);
  font-family: var(--font-mono);
  font-size: var(--font-size-small);
}

/* 表格响应式处理 */
.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  overflow-x: auto;
  display: block;
}

.markdown-content :deep(td),
.markdown-content :deep(th) {
  border: 1px solid var(--border-color);
  padding: 0.5em 0.8em;
  text-align: left;
  min-width: 80px;
}

/* 链接样式优化 */
.markdown-content :deep(a) {
  color: var(--accent-color);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: var(--accent-color);
}

/* 暗色主题支持 */
@media (prefers-color-scheme: dark) {
  .markdown-content {
    --text-primary: #e4e6eb;
    --text-secondary: #b0b3b8;
    --bg-code: #3a3b3c;
    --border-color: #4e4f50;
    --accent-color: #5a9fd4;
  }
}

/* 暗色主题强制类 */
.markdown-content.dark-theme {
  --text-primary: #e4e6eb;
  --text-secondary: #b0b3b8;
  --bg-code: #3a3b3c;
  --border-color: #4e4f50;
  --accent-color: #5a9fd4;
}

/* 响应式断点 */
@media (max-width: 768px) {
  .markdown-content {
    padding: 0 0.5rem;
  }
  
  .markdown-content :deep(pre) {
    font-size: 12px;
    padding: 0.8rem;
  }
  
  .markdown-content :deep(table) {
    font-size: 14px;
  }
}

/* 错误状态样式 */
.error-content {
  background: #fee;
  color: #c33;
  padding: 1rem;
  border-radius: 4px;
  border-left: 3px solid #c33;
}

/* 懒加载动画 */
.markdown-content {
  opacity: 0.7;
  transition: opacity 0.3s ease;
}

.markdown-content.is-visible {
  opacity: 1;
}
</style>