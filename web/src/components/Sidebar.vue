<script setup lang="ts">
import {
  ArrowRight,
} from '@element-plus/icons-vue'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface Props {
  isCollapsed: boolean
}

interface MenuItemType {
  id: string
  title: string
  icon: string
  route: string
  badge?: number
}

defineProps<Props>()

const router = useRouter()
const route = useRoute()
const activeRoute = ref(route.path)

// 监听路由变化，更新活跃状态
watch(() => route.path, (newPath) => {
  activeRoute.value = newPath
})

// 菜单项配置
const menuItems = ref<MenuItemType[]>([
  {
    id: 'dashboard',
    title: '仪表板',
    icon: 'Grid',
    route: '/dashboard',
  },
  {
    id: 'gateway-config',
    title: '网关配置',
    icon: 'Setting',
    route: '/gateway-config',
    badge: 3,
  },
  {
    id: 'user-management',
    title: '用户管理',
    icon: 'User',
    route: '/user-management',
  },
  {
    id: 'tenant-management',
    title: '租户管理',
    icon: 'OfficeBuilding',
    route: '/tenant-management',
  },
])

// 有徽章的菜单项
const menuItemsWithBadge = computed(() =>
  menuItems.value.filter(item => item.badge),
)

// 处理菜单选择
function handleMenuSelect(index: string) {
  activeRoute.value = index
  // 执行路由导航
  router.push(index)
}
</script>

<template>
  <div class="h-full flex flex-col bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm border-r border-gray-200/50 dark:border-gray-700/50 relative">
    <!-- 侧边栏菜单 -->
    <div class="flex-1 overflow-y-auto">
      <el-menu
        :default-active="activeRoute"
        class="sidebar-menu border-0"
        :collapse="isCollapsed"
        :collapse-transition="false"
        background-color="transparent"
        text-color="var(--el-text-color-primary)"
        active-text-color="var(--el-color-primary)"
        @select="handleMenuSelect"
      >
        <div class="p-4">
          <div class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-3">
            <span v-if="!isCollapsed">导航菜单</span>
          </div>
        </div>

        <el-menu-item
          v-for="item in menuItems"
          :key="item.id"
          :index="item.route"
          class="mx-3 my-1 rounded-lg transition-all duration-200 hover:scale-102 group"
          :class="[
            activeRoute === item.route
              ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/25'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700/70',
          ]"
        >
          <template #title>
            <div class="flex items-center justify-between w-full">
              <div class="flex items-center">
                <!-- 图标容器 -->
                <div
                  class="w-8 h-8 rounded-lg flex-center mr-3 transition-all duration-200"
                  :class="[
                    activeRoute === item.route
                      ? 'bg-white/20 text-white'
                      : 'text-gray-500 dark:text-gray-400 group-hover:text-blue-500 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/20',
                  ]"
                >
                  <el-icon :size="18">
                    <component :is="item.icon" />
                  </el-icon>
                </div>

                <!-- 菜单标题 -->
                <span
                  class="font-medium transition-all duration-200"
                  :class="[
                    activeRoute === item.route
                      ? 'text-white font-semibold'
                      : 'text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white',
                  ]"
                >
                  {{ item.title }}
                </span>
              </div>

              <!-- 徽章 -->
              <el-badge
                v-if="item.badge && !isCollapsed"
                :value="item.badge"
                :max="99"
                class="menu-badge"
                :class="[
                  activeRoute === item.route
                    ? 'opacity-90'
                    : 'opacity-80 group-hover:opacity-100',
                ]"
              />
            </div>
          </template>

          <!-- 图标（仅在折叠时显示） -->
          <div
            v-if="isCollapsed"
            class="w-8 h-8 rounded-lg flex-center transition-all duration-200"
            :class="[
              activeRoute === item.route
                ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md'
                : 'text-gray-500 dark:text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20',
            ]"
          >
            <el-icon :size="18">
              <component :is="item.icon" />
            </el-icon>
          </div>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 底部用户信息 -->
    <div v-if="!isCollapsed" class="p-4 border-t border-gray-200/50 dark:border-gray-700/50 bg-gradient-to-r from-gray-50 to-white dark:from-gray-800 dark:to-gray-700">
      <div class="user-profile p-3 rounded-xl bg-white/70 dark:bg-gray-700/70 backdrop-blur-sm border border-gray-200/50 dark:border-gray-600/50 hover:shadow-lg transition-all duration-300 cursor-pointer group">
        <div class="flex items-center space-x-3">
          <div class="relative">
            <el-avatar
              :size="36"
              src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=36&h=36&fit=crop&crop=face&auto=format"
              class="ring-2 ring-blue-500/20 group-hover:ring-blue-500/40 transition-all"
            />
            <!-- 在线状态指示器 -->
            <div class="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full ring-2 ring-white dark:ring-gray-700" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-900 dark:text-white truncate">
              John Doe
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 truncate">
              john@example.com
            </div>
          </div>
          <el-icon
            class="text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
            size="16"
          >
            <ArrowRight />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 折叠状态下的徽章 -->
    <div v-if="isCollapsed" class="absolute top-0 right-0 pt-20 pr-2 space-y-14">
      <div
        v-for="item in menuItemsWithBadge"
        :key="item.id"
        class="relative"
      >
        <el-badge
          :value="item.badge"
          :max="9"
          class="animate-bounce"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
}

.user-profile {
  position: relative;
  overflow: hidden;
}

.user-profile::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s;
}

.user-profile:hover::before {
  left: 100%;
}

/* 自定义菜单项样式 */
:deep(.el-menu-item) {
  height: auto !important;
  line-height: 1.5 !important;
  padding: 12px 16px !important;
  margin: 4px 12px !important;
  border-radius: 12px !important;
  border: none !important;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%) !important;
  color: white !important;
}

:deep(.el-menu-item:hover) {
  background-color: var(--el-fill-color-light) !important;
  transform: translateX(4px);
}

:deep(.el-menu--collapse .el-menu-item) {
  padding: 0 !important;
  margin: 4px 8px !important;
  width: 48px !important;
  height: 48px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* 徽章样式 */
:deep(.el-badge__content) {
  background-color: #f56565 !important;
  border: 2px solid white !important;
  font-weight: 600 !important;
  font-size: 10px !important;
}
</style>
