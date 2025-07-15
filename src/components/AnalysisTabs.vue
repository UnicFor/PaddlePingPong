<template>
  <div class="analysis-tabs">
    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab"
        :class="{ active: activeTab === tab }"
        @click="activeTab = tab"
      >
        {{ tab }}
      </button>
    </div>

    <div class="tab-content">
      <!-- 保持原有模板内容 -->
    </div>
  </div>
</template>

<script setup>
  import { ref } from 'vue'

  const activeTab = ref('分析报告')
  const tabs = ref(['分析报告', '动作分析', '可视化图表'])

</script>


<style scoped src="@/assets/css/analysis-tab.css"></style>