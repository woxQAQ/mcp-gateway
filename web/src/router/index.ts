import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../components/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('../components/Dashboard.vue'),
      },
      {
        path: '/mcp-config',
        name: 'McpConfig',
        component: () => import('../components/McpConfig.vue'),
      },
    ],
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫
router.beforeEach(async (to, _from, next) => {
  const { isAuthenticated, fetchCurrentUser } = useAuth()

  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    if (!isAuthenticated.value) {
      // 尝试获取当前用户信息
      try {
        await fetchCurrentUser()
      }
      catch {
        // 认证失败，重定向到登录页
        next('/login')
        return
      }
    }
  }

  // 如果已经认证但访问登录页，重定向到首页
  if (to.path === '/login' && isAuthenticated.value) {
    next('/dashboard')
    return
  }

  next()
})

export default router
