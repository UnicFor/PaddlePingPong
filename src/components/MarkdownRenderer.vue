<template>
  <div class="markdown-content" v-html="compiledMarkdown"></div>
</template>

<script>
import { marked } from 'marked'
import DOMPurify from 'dompurify'

export default {
  props: {
    content: {
      type: String,
      required: true
    }
  },
  computed: {
    compiledMarkdown() {
      const preprocessed = this.content
        .replace(/^(#{1,6}) /gm, '$1 ')
        .replace(/\*\*(.*?)\*\*/g, '**$1**');

      return DOMPurify.sanitize(
        marked.parse(preprocessed, {
          breaks: true,
          gfm: true
        })
      )
    }
  }
}
</script>

<style scoped>
.markdown-content :deep(h1) {
  font-size: 2em;
  margin: 0.67em 0;
  color: #2c3e50;
  border-bottom: 2px solid #eee;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
  margin: 0.83em 0;
  color: #34495e;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h3) {
  font-size: 1.17em;
  margin: 1em 0;
  color: #3b4a54;
}

.markdown-content :deep(h4) {
  font-size: 1em;
  margin: 1.33em 0;
  color: #4a5a65;
}

.markdown-content :deep(h5) {
  font-size: 0.83em;
  margin: 1.67em 0;
  color: #586872;
}

.markdown-content :deep(h6) {
  font-size: 0.67em;
  margin: 2.33em 0;
  color: #65737e;
}

.markdown-content :deep(strong) {
  color: #34495e;
  font-weight: 600;
}

.markdown-content :deep(ul) {
  padding-left: 1.2em;
  margin: 0.8em 0;
  list-style-type: disc;
}

.markdown-content :deep(li) {
  margin: 0.4em 0;
  line-height: 1.6;
}

.markdown-content :deep(code:not(pre code)) {
  background: #f8f9fa;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: Menlo, Consolas, monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: #f8f9fa;
  padding: 1em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
  line-height: 1.5;
}

.markdown-content :deep(pre code) {
  display: block;
  padding: 0;
  background: transparent;
  font-size: 0.9em;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #4a90e2;
  padding: 0.5em 1em;
  margin: 1em 0;
  background: #f8f9fa;
  color: #666;
}
</style>