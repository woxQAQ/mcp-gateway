<script setup lang="ts">
import type { HttpServer, McpConfigModel, McpServer, Router, TenantModel, Tool } from '../../generated/types'
import { Download, Plus, Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { importOpenapiApiV1OpenapiOpenapiImportPost } from '../../generated/api/openapi/openapi.gen'
import { listTenantsApiV1TenantTenantsGet } from '../../generated/api/tenant/tenant.gen'
import { useMcp } from '../stores/mcp'

// MCP store
const {
  configs,
  loading,
  fetchConfigs,
  createConfig,
  updateConfig,
  deleteConfig: deleteMcpConfig,
  activateConfig: activateMcpConfig,
  syncConfig: syncMcpConfig,
} = useMcp()

// 租户相关状态
const tenants = ref<TenantModel[]>([])
const tenantLoading = ref(false)

// 筛选状态
const selectedTenant = ref('')

// 对话框状态
const showCreateDialog = ref(false)
const showImportDialog = ref(false)
const editMode = ref(false)

// 表单数据
const configForm = ref<{
  name: string
  tenant_name: string
  servers: McpServer[]
  routers: Router[]
  tools: Tool[]
  http_servers: HttpServer[]
}>({
  name: '',
  tenant_name: '',
  servers: [],
  routers: [],
  tools: [],
  http_servers: [],
})

// OpenAPI 导入表单
const importForm = ref({
  file: null as File | null,
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 获取租户列表
async function fetchTenants() {
  tenantLoading.value = true
  try {
    const response = await listTenantsApiV1TenantTenantsGet({
      include_inactive: false, // 只获取活跃租户
    })

    if (response.status === 200) {
      tenants.value = response.data.tenants
    }
    else {
      ElMessage.error('获取租户列表失败')
    }
  }
  catch {
    ElMessage.error('获取租户列表失败')
  }
  finally {
    tenantLoading.value = false
  }
}

// 刷新配置列表
async function refreshConfigs() {
  try {
    await fetchConfigs(selectedTenant.value || undefined)
    total.value = configs.value.length
  }
  catch {
    ElMessage.error('获取配置列表失败')
  }
}

// 租户筛选处理
async function handleTenantFilter() {
  await refreshConfigs()
}

// 导入 OpenAPI 文档
async function importOpenAPI() {
  try {
    // 当前 API 只支持文件上传，不支持 URL
    if (!importForm.value.file) {
      ElMessage.error('请选择要导入的文件')
      return
    }

    // 使用默认租户
    const _tenantName = 'default'

    ElMessage.info('正在导入 OpenAPI 文档...')

    // 调用后端 API 导入 OpenAPI 文档
    const response = await importOpenapiApiV1OpenapiOpenapiImportPost({
      file: importForm.value.file,
    })

    if (response.status === 200) {
      ElMessage.success('OpenAPI 文档导入成功！系统已自动生成 MCP 配置')
      showImportDialog.value = false
      resetImportForm()
      await refreshConfigs()
    }
    else {
      ElMessage.error('导入失败，请检查文件格式')
    }
  }
  catch (error: any) {
    console.error('OpenAPI 导入失败:', error)

    // 处理不同类型的错误
    if (error.response?.data?.detail) {
      ElMessage.error(`导入失败: ${error.response.data.detail}`)
    }
    else if (error.message) {
      ElMessage.error(`导入失败: ${error.message}`)
    }
    else {
      ElMessage.error('导入失败，请稍后重试')
    }
  }
}

// 文件上传处理
function handleFileChange(file: File | null) {
  importForm.value.file = file
}

// 重置导入表单
function resetImportForm() {
  importForm.value = {
    file: null,
  }
}

// 编辑配置
function editConfig(config: McpConfigModel) {
  editMode.value = true
  configForm.value = {
    name: config.name,
    tenant_name: getTenantDisplayName(config.tenant_name),
    servers: config.servers || [],
    routers: config.routers || [],
    tools: config.tools || [],
    http_servers: config.http_servers || [],
  }
  showCreateDialog.value = true
}

// 保存配置
async function saveConfig() {
  try {
    const configData = {
      ...configForm.value,
      tenant_name: getTenantId(configForm.value.tenant_name),
    }

    if (editMode.value) {
      await updateConfig(configData as any)
      ElMessage.success('配置更新成功')
    }
    else {
      await createConfig(configData as any)
      ElMessage.success('配置创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    await refreshConfigs()
  }
  catch {
    ElMessage.error('保存失败')
  }
}

// 激活配置
async function activateConfig(config: McpConfigModel) {
  try {
    await activateMcpConfig(config.tenant_name, config.name)
    ElMessage.success('配置激活成功')
  }
  catch {
    ElMessage.error('激活失败')
  }
}

// 同步配置
async function syncConfig(config: McpConfigModel) {
  try {
    await syncMcpConfig(config.id)
    ElMessage.success('配置同步成功')
  }
  catch {
    ElMessage.error('同步失败')
  }
}

// 删除配置
async function deleteConfig(config: McpConfigModel) {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置 "${config.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    await deleteMcpConfig(config.tenant_name, config.name)
    ElMessage.success('配置删除成功')
    await refreshConfigs()
  }
  catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 重置表单
function resetForm() {
  editMode.value = false
  configForm.value = {
    name: '',
    tenant_name: '',
    servers: [],
    routers: [],
    tools: [],
    http_servers: [],
  }
}

// 分页处理
function handleSizeChange(val: number) {
  pageSize.value = val
  refreshConfigs()
}

function handleCurrentChange(val: number) {
  currentPage.value = val
  refreshConfigs()
}

// 获取租户显示名称
function getTenantDisplayName(tenantId: string) {
  const tenant = tenants.value.find(t => t.id === tenantId || t.name === tenantId)
  return tenant?.name || tenantId
}

// 获取租户ID（如果传入的是名称）
function getTenantId(tenantNameOrId: string) {
  const tenant = tenants.value.find(t => t.name === tenantNameOrId || t.id === tenantNameOrId)
  return tenant?.name || tenantNameOrId // 这里根据后端 API 的要求返回 name 或 id
}

// 初始化
onMounted(async () => {
  await Promise.all([
    refreshConfigs(),
    fetchTenants(),
  ])
})
</script>

<template>
  <div class="gateway-config-container p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        网关配置管理
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        导入OpenAPI文档，转换为MCP配置并管理网关服务配置
      </p>
    </div>

    <!-- 头部操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div class="flex space-x-2 items-center">
        <el-select
          v-model="selectedTenant"
          placeholder="选择租户筛选"
          clearable
          :loading="tenantLoading"
          style="width: 180px"
          @change="handleTenantFilter"
        >
          <el-option
            v-for="tenant in tenants"
            :key="tenant.id"
            :label="tenant.name"
            :value="tenant.name"
          />
        </el-select>
        <el-button type="success" @click="showImportDialog = true">
          <Upload />
          导入OpenAPI
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <Plus />
          新建配置
        </el-button>
      </div>

      <el-button @click="refreshConfigs">
        <Refresh />
        刷新
      </el-button>
    </div>

    <!-- 配置列表 -->
    <el-card class="shadow-md">
      <el-table
        v-loading="loading"
        :data="configs"
        style="width: 100%"
        stripe
        class="config-table"
      >
        <el-table-column prop="name" label="配置名称" width="200" />
        <el-table-column prop="tenant_name" label="租户名称" width="150">
          <template #default="{ row }">
            {{ getTenantDisplayName(row.tenant_name) }}
          </template>
        </el-table-column>
        <el-table-column prop="gmt_created" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.gmt_created).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="servers" label="服务器数量" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.servers?.length || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tools" label="工具数量" width="120">
          <template #default="{ row }">
            <el-tag type="success">
              {{ row.tools?.length || 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editConfig(row)">
              编辑
            </el-button>
            <el-button size="small" type="success" @click="activateConfig(row)">
              激活
            </el-button>
            <el-button size="small" type="warning" @click="syncConfig(row)">
              同步
            </el-button>
            <el-button size="small" type="danger" @click="deleteConfig(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="mt-4 flex justify-center">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- OpenAPI导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入OpenAPI文档"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="importForm">
        <el-form-item>
          <el-card class="upload-card" shadow="never">
            <div class="upload-area">
              <el-upload
                drag
                :auto-upload="false"
                :show-file-list="true"
                :limit="1"
                accept=".json,.yaml,.yml"
                :on-change="(file: any) => handleFileChange(file.raw)"
                :on-remove="() => handleFileChange(null)"
              >
                <div class="text-center p-3">
                  <el-icon :size="60" class="text-gray-400 mb-1">
                    <Download />
                  </el-icon>
                  <div class="text-sm text-gray-400 mb-1">
                    将 OpenAPI 文件拖到此处，或<em>点击上传</em>
                  </div>
                  <div class="text-xs text-gray-400">
                    支持 .json, .yaml, .yml 格式，最大 5MB
                  </div>
                </div>
              </el-upload>
            </div>
          </el-card>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportDialog = false">取消</el-button>
          <el-button type="primary" @click="importOpenAPI">
            导入并转换
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 创建/编辑配置对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editMode ? '编辑配置' : '新建配置'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="configForm" label-width="100px">
        <el-form-item label="配置名称" required>
          <el-input v-model="configForm.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="租户名称" required>
          <el-select
            v-model="configForm.tenant_name"
            placeholder="请选择租户"
            :loading="tenantLoading"
            :disabled="editMode"
            clearable
            filterable
          >
            <el-option
              v-for="tenant in tenants"
              :key="tenant.id"
              :label="tenant.name"
              :value="tenant.name"
            />
          </el-select>
          <div v-if="editMode" class="text-xs text-gray-500 mt-1">
            编辑模式下租户不可修改
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConfig">
            {{ editMode ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.gateway-config-container {
  background: #f8fafc;
  min-height: 100vh;
}

.config-table {
  background: white;
  border-radius: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.upload-card {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s ease;
  width: 100%;
  margin: 0;
}

.upload-card:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.upload-area {
  padding: 4px;
  width: 100%;
}

/* 确保上传区域占满对话框宽度 */
.upload-card .el-card__body {
  padding: 0;
  width: 100%;
}

/* 确保el-upload占满宽度并居中 */
.upload-area .el-upload-dragger {
  width: 100% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

/* 移除form-item的默认边距，让上传区域占满对话框 */
.el-dialog .el-form .el-form-item {
  margin-bottom: 0;
}

.el-dialog .el-form .el-form-item__content {
  width: 100%;
}
</style>
