<template>
  <div class="progress">
    <div class="progress-bar" :style="{ height: `${props.value}%` }" v-if="props.value > 0">
      <span class="progress-value" v-if="props.value >= 10">{{ props.value }}%</span>
    </div>
  </div>
</template>

<script lang='ts' setup>
const props = defineProps<{
  value: number
}>()
</script>

<style lang='scss' scoped>
.progress {
  border-radius: 4px;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
}

.progress-bar {
  border-radius: 4px;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: end;
  padding-bottom: 6px;
  align-items: center;
  background-color: var(--theme-primary-color);
  background-image: linear-gradient(45deg, rgba(255, 255, 255, 0.5) 25%,
      transparent 25%,
      transparent 50%,
      rgba(255, 255, 255, 0.5) 50%,
      rgba(255, 255, 255, 0.5) 75%,
      transparent 75%,
      transparent);
  transition: height 0.6s ease;
  background-size: 100% 40px;
  animation: progress-bar-animation 2s linear infinite;
}

.progress-value {
  color: white;
  font-size: var(--font-size-rank-2)
}

@keyframes progress-bar-animation {
  from {
    background-position: 0 40px;
  }

  to {
    background-position: 0 0;
  }
}
</style>
