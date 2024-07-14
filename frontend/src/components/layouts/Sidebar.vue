<template>
  <div class="sidebar-container">
    <div class="menu-title">
      <span class="content">菜单</span>
    </div>
    <div class="sidebar-item" v-for="(item, index) in menuList" :class="menuItemStyle(index)"
      @click="handleClick(index)">
      <el-icon :size="18" class="icon">
        <component :is="item.icon"></component>
      </el-icon>
      <span class="content">{{ item.name }}</span>
    </div>
  </div>
</template>

<script lang='ts' setup>
import router from '@/router';
import { Tools, Histogram } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useModel } from '@/stores/counter';
import { storeToRefs } from 'pinia';
import { ElMessage } from 'element-plus';
import 'element-plus/theme-chalk/el-message.css';
const useModelStore = useModel()
const { running } = storeToRefs(useModelStore)

const menuList = ref([{
  name: "模拟调度",
  icon: Tools
}, {
  name: '结果分析',
  icon: Histogram
}])
const routes = ref(['/dashboard', '/result'])
const activeIndex = ref(0)

const menuItemStyle = (index: number) => {
  if (index === activeIndex.value) {
    return 'sidebar-item-active'
  } else {
    return 'sidebar-item'
  }
}

const handleClick = (index: number) => {
  if (running.value) {
    ElMessage.error('请先停止模拟调度')
  } else {
    activeIndex.value = index
    const route = routes.value[index]
    router.push(route)
  }
}
</script>

<style lang='scss' scoped>
.sidebar-container {
  grid-area: sidebar;
  border-right: 1px solid var(--vt-c-divider-light-2);
  z-index: 10;
  display: flex;
  flex-direction: column;
}

.menu-title {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;

  .content {
    font-size: var(--font-size-rank-1);
    color: var(--theme-primary-color);
    font-weight: 600;
  }
}

.sidebar-item {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: left;
  padding: 0 20px;
  cursor: pointer;
  transition: all 0.2s ease;

  .content {
    font-size: var(--font-size-rank-2);
    color: var(--color-text);
    transition: all 0.2s ease;
  }

  .icon {
    transition: all 0.2s ease;
    margin-right: 12px;
  }
}

.sidebar-item:hover {
  transition: all 0.2s ease;
  background-color: rgba(49, 108, 114, 0.1);

  .content {
    transition: all 0.2s ease;
    color: var(--theme-primary-color);
  }

  .icon {
    transition: all 0.2s ease;
    margin-right: 12px;
    color: var(--theme-primary-color);
  }
}

.sidebar-item-active {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: left;
  padding: 0 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: rgba(49, 108, 114, 0.1);

  .content {
    transition: all 0.2s ease;
    color: var(--theme-primary-color);
    font-size: var(--font-size-rank-2);
  }

  .icon {
    transition: all 0.2s ease;
    margin-right: 12px;
    color: var(--theme-primary-color);
  }
}
</style>
