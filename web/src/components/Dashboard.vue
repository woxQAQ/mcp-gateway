<script setup lang="ts">
import {
  ArrowDown,
  ArrowRight,
  ArrowUp,
  Plus,
  Refresh,
  TrendCharts,
} from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

// 导入API stores
import { useAuth } from '../stores/auth'
import { useMcp } from '../stores/mcp'

const router = useRouter()

const chartPeriod = ref('7d')

// 使用stores
const { user, fetchCurrentUser } = useAuth()
const { configs, configCount, fetchConfigs } = useMcp()

// 动态统计数据
const stats = computed(() => [
  {
    id: 'gateway-configs',
    label: '网关配置',
    value: configCount.value?.toString() || '0',
    change: '+0%',
    trend: 'up',
    icon: 'Setting',
    color: '#409EFF',
  },
  {
    id: 'users',
    label: '系统用户',
    value: '3',
    change: '+2',
    trend: 'up',
    icon: 'User',
    color: '#67C23A',
  },
  {
    id: 'tenants',
    label: '租户数量',
    value: '3',
    change: '+1',
    trend: 'up',
    icon: 'OfficeBuilding',
    color: '#E6A23C',
  },
  {
    id: 'api-endpoints',
    label: 'API端点',
    value: configs.value?.reduce((sum, config) => sum + (config.tools?.length || 0), 0)?.toString() || '0',
    change: '+0%',
    trend: 'up',
    icon: 'Connection',
    color: '#F56C6C',
  },
])

// 用户显示名称
const displayName = computed(() => user?.username || '用户')

// 页面初始化
onMounted(async () => {
  await refreshData()
})

// 最近活动
const activities = ref([
  {
    id: 1,
    title: '网关配置已创建',
    description: '新的API网关配置已成功创建并激活',
    time: '2分钟前',
    type: 'success',
    icon: 'SuccessFilled',
  },
  {
    id: 2,
    title: '用户登录',
    description: 'admin 用户成功登录系统',
    time: '5分钟前',
    type: 'info',
    icon: 'InfoFilled',
  },
  {
    id: 3,
    title: 'OpenAPI导入',
    description: '成功导入并转换OpenAPI文档为MCP配置',
    time: '10分钟前',
    type: 'success',
    icon: 'SuccessFilled',
  },
  {
    id: 4,
    title: '租户状态变更',
    description: '企业租户B的状态已更新为暂停',
    time: '15分钟前',
    type: 'warning',
    icon: 'WarningFilled',
  },
])

// 快速操作
const quickActions = ref([
  {
    id: 'import-openapi',
    title: '导入OpenAPI',
    description: '导入OpenAPI文档并转换为网关配置',
    icon: 'Upload',
    color: '#409EFF',
  },
  {
    id: 'create-user',
    title: '创建用户',
    description: '添加新的平台用户账户',
    icon: 'UserFilled',
    color: '#67C23A',
  },
  {
    id: 'manage-tenants',
    title: '管理租户',
    description: '查看和管理平台租户配置',
    icon: 'OfficeBuilding',
    color: '#E6A23C',
  },
])

// 处理快速操作点击
function handleQuickAction(action: any) {
  switch (action.id) {
    case 'import-openapi':
      router.push('/gateway-config')
      break
    case 'create-user':
      router.push('/user-management')
      break
    case 'manage-tenants':
      router.push('/tenant-management')
      break
    default:
      console.error('Unknown quick action:', action.id)
  }
}

// 刷新数据
async function refreshData() {
  try {
    await Promise.all([
      fetchCurrentUser(),
      fetchConfigs(),
    ])
  }
  catch (error) {
    console.error('Refresh data failed:', error)
  }
}

// 返回操作
function goBack() {
  router.go(-1)
}

// 加载图表数据
async function loadChartData() {
  await refreshData()
}
</script>

<template>
  <div class="dashboard-container min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
    <!-- 页面标题 -->
    <div class="mb-6">
      <el-page-header content="仪表板" class="mb-4" @back="goBack">
        <template #extra>
          <el-button-group>
            <el-button class="shadow-sm" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="primary" class="shadow-sm" @click="() => router.push('/gateway-config')">
              <el-icon><Plus /></el-icon>
              导入OpenAPI
            </el-button>
          </el-button-group>
        </template>
      </el-page-header>

      <!-- 欢迎信息 -->
      <div class="glass-20 rounded-xl p-6 mb-6 border border-white/20">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          欢迎回来，{{ displayName }}！ 👋
        </h1>
        <p class="text-gray-600 dark:text-gray-400">
          系统运行良好，今天有 <span class="text-primary-500 font-semibold">2个新的</span> 网关配置更新
        </p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mb-6">
      <el-col v-for="stat in stats" :key="stat.id" :xs="12" :sm="6">
        <el-card
          class="stat-card hover:scale-105 transition-transform duration-300 cursor-pointer border-0 shadow-lg"
          :body-style="{ padding: '24px' }"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center mb-3">
                <div
                  class="w-12 h-12 rounded-xl flex-center shadow-sm"
                  :style="{ backgroundColor: `${stat.color}15`, color: stat.color }"
                >
                  <el-icon :size="24">
                    <component :is="stat.icon" />
                  </el-icon>
                </div>
              </div>
              <div class="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                {{ stat.value }}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-2">
                {{ stat.label }}
              </div>
              <div class="flex items-center text-xs">
                <span
                  class="flex items-center px-2 py-1 rounded-full"
                  :class="stat.trend === 'up' ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300'"
                >
                  <el-icon :size="12" class="mr-1">
                    <ArrowUp v-if="stat.trend === 'up'" />
                    <ArrowDown v-else />
                  </el-icon>
                  {{ stat.change }}
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表和活动区域 -->
    <el-row :gutter="20" class="mb-6">
      <!-- 系统活动图表 -->
      <el-col :xs="24" :lg="16">
        <el-card class="shadow-lg border-0">
          <template #header>
            <div class="flex-between">
              <div class="flex items-center">
                <div class="w-4 h-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mr-3" />
                <span class="text-lg font-semibold text-gray-900 dark:text-white">系统活动趋势</span>
              </div>
              <el-select v-model="chartPeriod" size="small" class="w-32">
                <el-option label="最近7天" value="7d" />
                <el-option label="最近30天" value="30d" />
                <el-option label="最近90天" value="90d" />
              </el-select>
            </div>
          </template>
          <div class="chart-container h-80 flex-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg">
            <div class="text-center">
              <el-icon :size="48" color="#c0c4cc">
                <TrendCharts />
              </el-icon>
              <p class="mt-4 text-gray-500 dark:text-gray-400">
                图表数据加载中...
              </p>
              <el-button type="primary" size="small" class="mt-3" @click="loadChartData">
                加载图表数据
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 最近活动 -->
      <el-col :xs="24" :lg="8">
        <el-card class="shadow-lg border-0 h-full">
          <template #header>
            <div class="flex-between">
              <div class="flex items-center">
                <div class="w-4 h-4 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full mr-3" />
                <span class="text-lg font-semibold text-gray-900 dark:text-white">最近活动</span>
              </div>
              <el-link type="primary" :underline="false" class="text-sm">
                查看全部
              </el-link>
            </div>
          </template>
          <el-timeline class="px-2">
            <el-timeline-item
              v-for="activity in activities"
              :key="activity.id"
              :timestamp="activity.time"
              :type="activity.type"
              placement="top"
            >
              <el-card
                class="activity-card p-4 border-l-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                :class="{
                  'border-l-green-400 bg-green-50 dark:bg-green-900/20': activity.type === 'success',
                  'border-l-yellow-400 bg-yellow-50 dark:bg-yellow-900/20': activity.type === 'warning',
                  'border-l-blue-400 bg-blue-50 dark:bg-blue-900/20': activity.type === 'info',
                  'border-l-red-400 bg-red-50 dark:bg-red-900/20': activity.type === 'danger',
                }"
                :body-style="{ padding: '0' }"
              >
                <div class="flex items-start">
                  <div
                    class="w-8 h-8 rounded-full flex-center mr-3 flex-shrink-0"
                    :class="{
                      'bg-green-100 text-green-600': activity.type === 'success',
                      'bg-yellow-100 text-yellow-600': activity.type === 'warning',
                      'bg-blue-100 text-blue-600': activity.type === 'info',
                      'bg-red-100 text-red-600': activity.type === 'danger',
                    }"
                  >
                    <el-icon :size="16">
                      <component :is="activity.icon" />
                    </el-icon>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-900 dark:text-white text-sm mb-1">
                      {{ activity.title }}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                      {{ activity.description }}
                    </div>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作面板 -->
    <el-card class="shadow-lg border-0">
      <template #header>
        <div class="flex items-center">
          <div class="w-4 h-4 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full mr-3" />
          <span class="text-lg font-semibold text-gray-900 dark:text-white">快速操作</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col v-for="action in quickActions" :key="action.id" :xs="24" :sm="8">
          <div
            class="group quick-action-card p-6 rounded-xl border border-gray-200 dark:border-gray-700 cursor-pointer transition-all duration-300 hover:shadow-xl hover:scale-105 hover:border-transparent bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-700"
            @click="handleQuickAction(action)"
          >
            <div class="flex items-center">
              <div
                class="w-12 h-12 rounded-xl flex-center mr-4 group-hover:scale-110 transition-transform duration-300"
                :style="{ backgroundColor: `${action.color}15`, color: action.color }"
              >
                <el-icon :size="24">
                  <component :is="action.icon" />
                </el-icon>
              </div>
              <div class="flex-1">
                <div class="font-semibold text-gray-900 dark:text-white mb-1">
                  {{ action.title }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  {{ action.description }}
                </div>
              </div>
              <el-icon
                class="text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all duration-300"
                :size="16"
              >
                <ArrowRight />
              </el-icon>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard-container {
  padding: 24px;
}

.glass-20 {
  backdrop-filter: blur(10px);
  background-color: rgba(255, 255, 255, 0.2);
}

.stat-card {
  height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.8) 100%);
}

.dark .stat-card {
  background: linear-gradient(135deg, rgba(31, 41, 55, 0.9) 0%, rgba(31, 41, 55, 0.8) 100%);
}

.activity-card {
  border: none !important;
}

.quick-action-card {
  position: relative;
  overflow: hidden;
}

.quick-action-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s;
}

.quick-action-card:hover::before {
  left: 100%;
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
}
</style>
