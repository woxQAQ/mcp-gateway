<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'

const isCollapsed = ref(false)
const isMobile = ref(false)
const isMobileMenuOpen = ref(false)

// 切换侧边栏
function toggleSidebar() {
  if (isMobile.value) {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
  }
  else {
    isCollapsed.value = !isCollapsed.value
  }
}

// 关闭移动端菜单
function closeMobileMenu() {
  isMobileMenuOpen.value = false
}

// 检查屏幕尺寸
function checkScreenSize() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    isMobileMenuOpen.value = false
  }
}

onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<template>
  <el-container class="layout-container">
    <!-- 顶部导航栏 -->
    <el-header class="layout-header">
      <Header @toggle-sidebar="toggleSidebar" />
    </el-header>

    <el-container>
      <!-- 侧边栏 -->
      <el-aside
        class="layout-aside"
        :width="isCollapsed ? '64px' : '240px'"
      >
        <Sidebar :is-collapsed="isCollapsed" />
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="layout-main">
        <slot />
      </el-main>
    </el-container>

    <!-- 移动端遮罩层 -->
    <div
      v-if="isMobileMenuOpen"
      class="mobile-overlay"
      @click="closeMobileMenu"
    />
  </el-container>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-header {
  padding: 0;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
}

.layout-aside {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s ease;
}

.layout-main {
  background: var(--el-bg-color-page);
  overflow-y: auto;
}

.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1999;
}

@media (max-width: 768px) {
  .layout-aside {
    position: fixed;
    top: 60px;
    left: 0;
    bottom: 0;
    z-index: 2000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }

  .layout-aside.mobile-open {
    transform: translateX(0);
  }
}
</style>
