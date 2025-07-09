import type { ApiError } from '../../mutator'
import { computed, ref } from 'vue'
import * as api from '../../generated/api/APIServer.gen'

// 用户数据类型 - 匹配后端UserModel
export interface User {
  id: string
  username: string
  email?: string
  role: 'normal' | 'admin'
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  is_staff: boolean
  date_joined: string
  gmt_created: string
  gmt_updated: string
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

    // 重新获取用户列表以确保数据一致性
    await fetchUsers()

    // 尝试从响应中提取用户信息
    const responseData = response.data as any
    return responseData?.user || responseData
  }
  catch (err: any) {
    const apiError = err as ApiError
    // 处理具体的错误信息
    if (apiError.status === 400) {
      if (apiError.message?.includes('already exists')) {
        error.value = '用户名或邮箱已存在'
      }
      else if (apiError.message?.includes('not match')) {
        error.value = '密码确认不匹配'
      }
      else {
        error.value = apiError.message || '用户信息无效'
      }
    }
    else {
      error.value = apiError.message || '创建用户失败'
    }
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
    // 处理具体的错误信息
    if (apiError.status === 403) {
      error.value = '权限不足：需要管理员权限才能删除用户'
    }
    else if (apiError.status === 400) {
      if (apiError.message?.includes('last admin')) {
        error.value = '无法删除最后一个管理员账户'
      }
      else if (apiError.message?.includes('yourself')) {
        error.value = '无法删除自己的账户'
      }
      else if (apiError.message?.includes('not found')) {
        error.value = '用户不存在'
      }
      else {
        error.value = apiError.message || '删除操作无效'
      }
    }
    else {
      error.value = apiError.message || '删除用户失败'
    }
    throw err
  }
  finally {
    loading.value = false
  }
}

// 更新用户状态
async function updateUserStatus(user: User, newStatus: boolean) {
  loading.value = true
  error.value = null

  try {
    const response = await api.updateUserStatusApiV1AuthUsersUserIdStatusPatch(
      user.id,
      { is_active: newStatus },
    )

    // 更新本地状态
    const userIndex = users.value.findIndex(u => u.id === user.id)
    if (userIndex !== -1 && response.data) {
      users.value[userIndex] = response.data as User
    }

    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    // 处理权限错误
    if (apiError.status === 403) {
      error.value = '权限不足：需要管理员权限才能修改用户状态'
    }
    else if (apiError.status === 400 && apiError.message?.includes('最后一个管理员')) {
      error.value = '无法禁用最后一个管理员账户'
    }
    else if (apiError.status === 400 && apiError.message?.includes('自己的状态')) {
      error.value = '无法修改自己的账户状态'
    }
    else {
      error.value = apiError.message || '更新用户状态失败'
    }
    throw err
  }
  finally {
    loading.value = false
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
