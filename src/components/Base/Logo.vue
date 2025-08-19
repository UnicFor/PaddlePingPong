<script setup></script>

<template>
  <span class="elegant-text">Paddle</span>
  <span> PingPong</span>
</template>

<style scoped>
.elegant-text {
  color: #2d3436;
  position: relative;
  display: inline-block;
}

.elegant-text::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 0;
  width: 100%;
  height: 3px;
  background: #2d3436;
  transition: transform 0.4s ease-in-out;
  transform: scaleX(1);
  transform-origin: left;
}

.elegant-text:hover::after {
  transform: scaleX(0);
  transform-origin: right;
}
</style>