import type { Mcp, McpConfigModel, McpConfigName } from '../../generated/types'
import type { ApiError } from '../../mutator'
// MCP配置管理状态
import { computed, ref } from 'vue'
import * as api from '../../generated/api/APIServer.gen'

// 状态
const configs = ref<McpConfigModel[]>([])
const configNames = ref<McpConfigName[]>([])
const currentConfig = ref<McpConfigModel | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// 计算属性
const configCount = computed(() => configs.value.length)

// 获取MCP配置列表
async function fetchConfigs(tenantId?: string) {
  loading.value = true
  error.value = null

  try {
    const response = await api.listMcpConfigsApiV1McpConfigsGet({ tenant_id: tenantId })
    configs.value = response.data
    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '获取配置列表失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 获取配置名称列表
async function fetchConfigNames(tenantId?: string, includeDeleted = false) {
  try {
    const response = await api.listMcpConfigNamesApiV1McpConfigsNamesGet({
      tenant_id: tenantId,
      include_deleted: includeDeleted,
    })
    configNames.value = response.data
    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '获取配置名称失败'
    throw err
  }
}

// 创建MCP配置
async function createConfig(config: Mcp) {
  loading.value = true
  error.value = null

  try {
    const response = await api.createMcpConfigApiV1McpConfigsPost(config)

    // 重新获取配置列表
    await fetchConfigs()

    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '创建配置失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 更新MCP配置
async function updateConfig(config: Mcp) {
  loading.value = true
  error.value = null

  try {
    const response = await api.updateMcpConfigApiV1McpConfigsPut(config)

    // 更新本地状态
    const index = configs.value.findIndex(c => c.name === config.name)
    if (index !== -1) {
      configs.value[index] = response.data
    }

    return response.data
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '更新配置失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 删除MCP配置
async function deleteConfig(tenantId: string, name: string) {
  loading.value = true
  error.value = null

  try {
    await api.deleteMcpConfigApiV1McpConfigsTenantIdNameDelete(tenantId, name)

    // 从本地状态中移除
    configs.value = configs.value.filter(c => !(c.tenant_name === tenantId && c.name === name))
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '删除配置失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 激活MCP配置
async function activateConfig(tenantName: string, name: string) {
  loading.value = true
  error.value = null

  try {
    await api.activeMcpConfigApiV1McpTenantNameNameActivePost(tenantName, name)
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '激活配置失败'
    throw err
  }
  finally {
    loading.value = false
  }
}

// 同步MCP配置
async function syncConfig(configId: string) {
  loading.value = true
  error.value = null

  try {
    await api.syncMcpConfigApiV1McpConfigsConfigIdSyncPost(configId)
  }
  catch (err: any) {
    const apiError = err as ApiError
    error.value = apiError.message || '同步配置失败'
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

// 设置当前配置
function setCurrentConfig(config: McpConfigModel | null) {
  currentConfig.value = config
}

// 导出状态和方法
export function useMcp() {
  return {
    // 状态
    configs,
    configNames,
    currentConfig,
    loading,
    error,
    configCount,

    // 方法
    fetchConfigs,
    fetchConfigNames,
    createConfig,
    updateConfig,
    deleteConfig,
    activateConfig,
    syncConfig,
    clearError,
    setCurrentConfig,
  }
}
