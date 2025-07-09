import type { ApiError } from '../../mutator'
import { computed, ref } from 'vue'
import * as api from '../../generated/api/APIServer.gen'

// 用户数据类型 - 匹配后端UserModel
export interface User {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
  date_joined: string
}

// 状态
const users = ref<User[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// 计算属性
const userCount = computed(() => users.value.length)
const activeUserCount = computed(() => users.value.filter(u => u.is_active).length)

// 获取用户列表
async function fetchUsers() {
  loading.value = true
  error.value = null

  try {
    const response = await api.listUsersApiV1AuthUsersGet()
    // 处理API响应数据结构
    if (response.data && typeof response.data === 'object' && 'users' in response.data) {
      const userList = (response.data as any).users
      users.value = Array.isArray(userList) ? userList : []
    }
    else {
      users.value = []
    }
    return users.value
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '获取用户列表失败'
    users.value = []
    throw err
  }
  finally {
    loading.value = false
  }
}

// 创建用户（使用注册API）
async function createUser(userData: {
  username: string
  email?: string
  password: string
  confirmPassword: string
}) {
  loading.value = true
  error.value = null

  try {
    const response = await api.registerApiV1AuthRegisterPost({
      username: userData.username,
      email: userData.email,
      password: userData.password,
      confirm_password: userData.confirmPassword,
    })

    // 重新获取用户列表
    await fetchUsers()
    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '创建用户失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 删除用户
async function deleteUser(userId: string) {
  loading.value = true
  error.value = null

  try {
    await api.deleteUserApiV1AuthUsersUserIdDelete(userId)

    // 从本地状态中移除
    users.value = users.value.filter(u => u.id !== userId)
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '删除用户失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 更新用户状态（模拟，后端暂无此API）
async function updateUserStatus(user: User, newStatus: boolean) {
  // 注意：后端目前没有更新用户状态的API
  // 这里只是本地更新，实际项目需要后端支持
  const userIndex = users.value.findIndex(u => u.id === user.id)
  if (userIndex !== -1) {
    users.value[userIndex].is_active = newStatus
  }
}

// 搜索用户（本地过滤）
function searchUsers(keyword: string) {
  if (!keyword.trim()) {
    return users.value
  }

  const lowerKeyword = keyword.toLowerCase()
  return users.value.filter(user =>
    user.username.toLowerCase().includes(lowerKeyword)
    || user.email?.toLowerCase().includes(lowerKeyword),
  )
}

// 清除错误
function clearError() {
  error.value = null
}

// 导出状态和方法
export function useUsers() {
  return {
    // 状态
    users,
    loading,
    error,
    userCount,
    activeUserCount,

    // 方法
    fetchUsers,
    createUser,
    deleteUser,
    updateUserStatus,
    searchUsers,
    clearError,
  }
}