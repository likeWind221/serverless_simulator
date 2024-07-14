<template>
  <div class="header-container">
    <div class="header-title">
      Severless计算环境-模拟器
    </div>
  </div>
</template>

<script lang='ts' setup>

</script>

<style lang='scss' scoped>
.header-container {
  grid-area: header;
  border-bottom: 1px solid var(--vt-c-divider-light-2);
  display: flex;
  align-items: center;
  justify-content: right;
  padding: 0 20px;
}

.header-title {
  color: var(--color-text);
  font-size: var(--font-size-rank-2);
}
</style>
