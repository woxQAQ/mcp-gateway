// API 客户端配置
// 用于 orval 生成的客户端代码

export type ErrorType<Error> = Error

// 自定义 fetch 实例配置
export function customInstance<T>(url: string, config?: RequestInit): Promise<T> {
  // 基础 URL 配置
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  // 构建完整 URL
  const fullUrl = url.startsWith('http') ? url : `${baseURL}${url}`

  // 默认请求配置
  const defaultConfig: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    ...config,
  }

  return fetch(fullUrl, defaultConfig)
    .then(async (response) => {
      // 检查响应状态
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // 处理不同的响应类型
      const contentType = response.headers.get('content-type')

      if (contentType?.includes('application/json')) {
        return response.json()
      }

      if (contentType?.includes('text/')) {
        return response.text()
      }

      return response.blob()
    })
    .catch((error) => {
      console.error('API request failed:', error)
      throw error
    })
}

// 获取认证头
function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token')

  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    }
  }

  return {}
}

// 设置认证令牌
export function setAuthToken(token: string) {
  localStorage.setItem('auth_token', token)
}

// 清除认证令牌
export function clearAuthToken() {
  localStorage.removeItem('auth_token')
}

// 错误处理类型
export interface ApiError {
  message: string
  status: number
  details?: any
}
