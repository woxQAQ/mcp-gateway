import type { ApiError, UserInfo } from '../../mutator'
// 用户认证状态管理
import { computed, ref } from 'vue'
import * as api from '../../generated/api/APIServer.gen'

// 用户状态
const user = ref<UserInfo | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// 计算属性
const isAuthenticated = computed(() => !!user.value)
const isLoading = computed(() => loading.value)

// 登录函数
async function login(username: string, password: string) {
  loading.value = true
  error.value = null

  try {
    const response = await api.loginApiV1AuthLoginPost({
      username,
      password,
    })

    // 登录成功后获取用户信息
    user.value = response.data as UserInfo
    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '登录失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 注册函数
async function register(username: string, password: string, confirmPassword: string, email?: string) {
  loading.value = true
  error.value = null

  try {
    // 手动调用注册API（暂时使用fetch直到重新生成客户端）
    const response = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        username,
        password,
        confirm_password: confirmPassword,
        email,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '注册失败')
    }

    const userData = await response.json()
    user.value = userData as UserInfo
    return userData
  }
  catch (err: any) {
    error.value = err.message || '注册失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 登出函数
async function logout() {
  loading.value = true

  try {
    await api.logoutApiV1AuthLogoutPost()
    user.value = null
  }
  catch (err: any) {
    console.error('Logout error:', err)
    // 即使登出API失败，也清除本地状态
    user.value = null
  }
  finally {
    loading.value = false
  }
}

// 获取当前用户信息
async function fetchCurrentUser() {
  loading.value = true
  error.value = null

  try {
    const response = await api.getUserApiV1AuthUserGet()
    user.value = response.data as UserInfo
    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    if (apiError.status === 401) {
      // 未认证，清除用户状态
      user.value = null
    }
    else {
      error.value = apiError.message || '获取用户信息失败'
    }
    throw err
  }
  finally {
    loading.value = false
  }
}

// 修改密码
async function changePassword(oldPassword: string, newPassword: string) {
  if (!user.value)
    throw new Error('用户未登录')

  loading.value = true
  error.value = null

  try {
    await api.changePasswordApiV1AuthUsersChangePasswordPost({
      username: user.value.username,
      old_password: oldPassword,
      new_password: newPassword,
    })
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '修改密码失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 清除错误
function clearError() {
  error.value = null
}

// 导出状态和方法
export function useAuth() {
  return {
    // 状态
    user: user.value,
    loading,
    error,
    isAuthenticated,
    isLoading,

    // 方法
    login,
    register,
    logout,
    fetchCurrentUser,
    changePassword,
    clearError,
  }
}
