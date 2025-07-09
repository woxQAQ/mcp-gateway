// API 客户端配置
// 用于 orval 生成的客户端代码

export type ErrorType<_e> = Error

// 自定义 fetch 实例配置
export function customInstance<T>(url: string, config?: RequestInit): Promise<T> {
  // 在开发环境使用代理，生产环境使用完整URL
  const isDev = import.meta.env.DEV
  const baseURL = isDev ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')

  // 构建完整 URL
  const fullUrl = url.startsWith('http') ? url : `${baseURL}${url}`

  // 默认请求配置
  const defaultConfig: RequestInit = {
    credentials: 'include', // 重要：包含cookies用于认证
    headers: {
      'Content-Type': 'application/json',
      ...config?.headers,
    },
    ...config,
  }

  return fetch(fullUrl, defaultConfig)
    .then(async (response) => {
      // 处理不同的响应类型
      const contentType = response.headers.get('content-type')

      let data: any
      if (contentType?.includes('application/json')) {
        data = await response.json()
      }
      else if (contentType?.includes('text/')) {
        data = await response.text()
      }
      else {
        data = await response.blob()
      }

      // 构建响应对象
      const result = {
        data,
        status: response.status,
        headers: response.headers,
      }

      // 检查响应状态
      if (!response.ok) {
        const error: ApiError = {
          message: data?.detail || `HTTP error! status: ${response.status}`,
          status: response.status,
          details: data,
        }
        throw error
      }

      return result as T
    })
    .catch((error) => {
      // 如果是我们抛出的ApiError，直接重新抛出
      if (error.status !== undefined) {
        throw error
      }

      // 否则包装为ApiError
      console.error('API request failed:', error)
      const apiError: ApiError = {
        message: error.message || 'Network error',
        status: 0,
        details: error,
      }
      throw apiError
    })
}

// 错误处理类型
export interface ApiError {
  message: string
  status: number
  details?: any
}

// 用户信息类型
export interface UserInfo {
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

// 响应包装类型
export interface ApiResponse<T = any> {
  data: T
  status: number
  headers: Headers
}
