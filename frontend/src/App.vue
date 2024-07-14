<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Header from '@/components/layouts/Header.vue'
import Sidebar from './components/layouts/Sidebar.vue';
</script>

<template>
  <Header />
  <Sidebar />
  <div class="content-container">
    <KeepAlive>
      <router-view v-slot="{ Component }">
        <transition name="fade">
          <component :is="Component" />
        </transition>
      </router-view>
    </KeepAlive>
  </div>
</template>

<style lang="scss" scoped>
.content-container {
  padding: 0px 12px;
  grid: main;
  background-color: var(--vt-c-background-light-1);
  overflow: auto;
}

.router-view {
  display: flex;
  flex-direction: column;
}

.fade-enter-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from {
  opacity: 0;
}
</style>
