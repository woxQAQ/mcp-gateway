<script setup lang="ts">
import {
  ArrowDown,
  Bell,
  Menu,
  Moon,
  Setting,
  Sunny,
  SwitchButton,
  User,
} from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

defineEmits(['toggleSidebar'])

const router = useRouter()
const { user, logout } = useAuth()

const isDark = ref(false)

// 切换主题
function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  // 保存到本地存储
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

// 计算用户显示名称
const displayName = computed(() => user.value?.username || '用户')
const userRole = computed(() => {
  const role = user.value?.role
  if (role === 'admin') {
    return '管理员'
  }
  if (role === 'normal') {
    return '普通用户'
  }
  return '用户'
})

// 处理用户菜单点击
async function handleUserMenuClick(command: string) {
  // 处理用户菜单点击逻辑
  switch (command) {
    case 'profile':
      // 跳转到个人资料
      break
    case 'settings':
      // 跳转到设置
      break
    case 'help':
      // 打开帮助中心
      break
    case 'logout':
      // 退出登录
      try {
        await logout()
        router.push('/login')
      }
      catch (error) {
        console.error('Logout failed:', error)
      }
      break
  }
}

// 初始化主题
function initTheme() {
  const savedTheme = localStorage.getItem('theme')
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  isDark.value = savedTheme === 'dark' || (!savedTheme && systemDark)
  document.documentElement.classList.toggle('dark', isDark.value)
}

// 页面加载时初始化主题
initTheme()
</script>

<template>
  <div class="h-16 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-200/50 dark:border-gray-700/50 flex-between px-6 relative z-50">
    <!-- 左侧区域 -->
    <div class="flex items-center space-x-4">
      <!-- 菜单按钮 -->
      <el-button
        type="text"
        class="menu-button hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg p-2 transition-colors"
        @click="$emit('toggleSidebar')"
      >
        <el-icon size="20">
          <Menu />
        </el-icon>
      </el-button>

      <!-- 品牌标识 -->
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-xl flex-center shadow-lg">
          <el-icon class="text-white" size="20">
            <Setting />
          </el-icon>
        </div>
        <div class="hidden sm:block">
          <h1 class="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            MCP Gateway
          </h1>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            管理系统
          </p>
        </div>
      </div>
    </div>

    <!-- 右侧区域 -->
    <div class="flex items-center space-x-3">
      <!-- 搜索框 (桌面端) -->
      <div class="hidden lg:block">
        <div class="relative">
          <input
            type="text"
            placeholder="搜索..."
            class="w-64 pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-gray-600 transition-all duration-200"
          >
          <div class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
      </div>

      <!-- 主题切换 -->
      <el-button
        type="text"
        class="w-10 h-10 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 flex-center transition-colors group"
        @click="toggleTheme"
      >
        <el-icon
          class="transition-transform group-hover:scale-110"
          size="18"
        >
          <Sunny v-if="isDark" />
          <Moon v-else />
        </el-icon>
      </el-button>

      <!-- 通知 -->
      <div class="relative">
        <el-badge :value="3" :max="99" class="notification-badge">
          <el-button
            type="text"
            class="w-10 h-10 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 flex-center transition-colors group"
          >
            <el-icon
              class="transition-transform group-hover:scale-110"
              size="18"
            >
              <Bell />
            </el-icon>
          </el-button>
        </el-badge>
        <!-- 通知脉冲效果 -->
        <div class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full animate-ping" />
      </div>

      <!-- 用户菜单 -->
      <el-dropdown trigger="click" @command="handleUserMenuClick">
        <div class="user-info flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors group">
          <el-avatar
            :size="32"
            src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face&auto=format"
            class="ring-2 ring-gray-200 dark:ring-gray-600 group-hover:ring-blue-500 transition-all"
          />
          <div class="hidden md:block text-left">
            <div class="text-sm font-medium text-gray-900 dark:text-white">
              {{ displayName }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ userRole }}
            </div>
          </div>
          <el-icon
            class="text-gray-400 transition-transform group-hover:rotate-180"
            size="14"
          >
            <ArrowDown />
          </el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu class="w-48">
            <el-dropdown-item command="profile" class="hover:bg-blue-50 dark:hover:bg-blue-900/20">
              <div class="flex items-center space-x-3">
                <el-icon class="text-blue-500">
                  <User />
                </el-icon>
                <span>个人资料</span>
              </div>
            </el-dropdown-item>
            <el-dropdown-item command="settings" class="hover:bg-green-50 dark:hover:bg-green-900/20">
              <div class="flex items-center space-x-3">
                <el-icon class="text-green-500">
                  <Setting />
                </el-icon>
                <span>账户设置</span>
              </div>
            </el-dropdown-item>
            <el-dropdown-item command="help" class="hover:bg-purple-50 dark:hover:bg-purple-900/20">
              <div class="flex items-center space-x-3">
                <el-icon class="text-purple-500">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z" />
                  </svg>
                </el-icon>
                <span>帮助中心</span>
              </div>
            </el-dropdown-item>
            <el-dropdown-item divided command="logout" class="hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600">
              <div class="flex items-center space-x-3">
                <el-icon class="text-red-500">
                  <SwitchButton />
                </el-icon>
                <span>退出登录</span>
              </div>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<style scoped>
.menu-button {
  font-size: 18px;
}

.notification-badge {
  position: relative;
}

/* 自定义下拉菜单动画 */
:deep(.el-dropdown-menu) {
  margin-top: 8px !important;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

/* 搜索框聚焦动画 */
input:focus {
  transform: scale(1.02);
}

/* 用户头像悬停效果 */
.user-info:hover .el-avatar {
  transform: scale(1.05);
}

@media (max-width: 640px) {
  .user-info {
    padding: 8px;
  }
}
</style>
