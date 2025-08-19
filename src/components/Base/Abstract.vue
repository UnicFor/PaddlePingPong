<script>
export default {
  data() {
    return {
      hoverIndex: null,
      title: "核心技术架构",
      subtitle: "基于飞桨与文心大模型的智能运动分析平台",
      featureCards: [
        {
          icon: "📹",
          title: "非接触式动作捕捉",
          items: ["多目标实时跟踪", "人体关键点识别", "击球姿态解算", "轨迹预测算法"],
          tags: [
            { name: "PaddlePaddle", type: "paddle" },
            { name: "PaddleDetection", type: "" },
            { name: "PPHuman", type: "" },
            { name: "PPTSM", type: "" },
            { name: "PP-TinyPose", type: "" },
          ]
        },
        {
          icon: "🧠",
          title: "运动效果评估",
          items: ["动作质量评分", "技战术分析", "训练建议生成", "多维度信息生成"],
          tags: [
            { name: "文心大模型", type: "wenxin" },
            { name: "Prompt Engineering", type: "" }
          ]
        },
        {
          icon: "📊",
          title: "多维度数据呈现",
          items: ["运动轨迹热力图", "动作角度呈现", "人体骨骼图标注", "模型调试数据"],
          tags: [
            { name: "Three.js", type: "" },
            { name: "ECharts", type: "" }
          ]
        }
      ],
      techStacks: [
        {
          name: "paddle",
          description: "飞桨深度学习框架"
        },
        {
          name: "wenxin",
          description: "文心大模型"
        }
      ]
    };
  }
};
</script>

<template>
  <section class="tech-intro">
    <div class="section-title">
      <h2>{{ title }}</h2>
      <p>{{ subtitle }}</p>
    </div>

    <div class="feature-cards">
      <div
        v-for="(card, index) in featureCards"
        :key="index"
        class="card"
        @mouseover="hoverIndex = index"
        @mouseleave="hoverIndex = null"
      >
        <div class="card-icon">{{ card.icon }}</div>
        <h3>{{ card.title }}</h3>
        <ul class="tech-list">
          <li v-for="(item, i) in card.items" :key="i">{{ item }}</li>
        </ul>
        <div class="tech-tag-group">
          <span
            v-for="(tag, t) in card.tags"
            :key="t"
            :class="['tech-tag', tag.type]"
          >
            {{ tag.name }}
          </span>
        </div>
      </div>
    </div>

    <div class="tech-stack">
      <div
        v-for="stack in techStacks"
        :key="stack.name"
        class="stack-item"
      >
        <p>{{ stack.description }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped src="@/assets/css/abstract.css"></style>