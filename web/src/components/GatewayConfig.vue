<script setup lang="ts">
import type { UploadInstance } from 'element-plus'
import type { BodyImportOpenapiApiV1OpenapiOpenapiImportPost, HttpServer, McpConfigModel, McpServer, Router, TenantModel, Tool } from '../../generated/types'
import { Delete, Download, Edit, Plus, Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { importOpenapiApiV1OpenapiOpenapiImportPost } from '../../generated/api/openapi/openapi.gen'
import { listTenantsApiV1TenantTenantsGet } from '../../generated/api/tenant/tenant.gen'
import { McpServerType, Policy } from '../../generated/types'
import { useMcp } from '../stores/mcp'

// 扩展导入表单类型，支持File类型和null初始值
interface ImportFormData {
  file: File | null
}

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
const importForm = ref<ImportFormData>({
  file: null,
})

// Upload组件引用
const uploadRef = ref<UploadInstance>()

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 新增：活动的选项卡
const activeTab = ref('basic')

// 新增：表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
  ],
  tenant_name: [
    { required: true, message: '请选择租户', trigger: 'change' },
  ],
}

// 新增：添加新项目的临时变量
const newServer = ref<McpServer>({
  name: '',
  description: '',
  type: McpServerType.stdio,
  command: '',
  args: [],
  url: '',
  policy: Policy.on_demand,
  preinstalled: false,
})

const newRouter = ref<Router>({
  prefix: '',
  server: '',
  sse_prefix: '',
  cors: null,
})

const newTool = ref<Tool>({
  name: '',
  description: '',
  method: 'GET',
  path: '',
  args: [],
  headers: {},
  input_schema: {},
  request_body: '',
  response_body: '',
})

const newHttpServer = ref<HttpServer>({
  name: '',
  description: '',
  url: '',
  tools: [],
})

// 新增：编辑模式标记
const editingServerIndex = ref(-1)
const editingRouterIndex = ref(-1)
const editingToolIndex = ref(-1)
const editingHttpServerIndex = ref(-1)

// 新增：显示添加对话框
const showAddServerDialog = ref(false)
const showAddRouterDialog = ref(false)
const showAddToolDialog = ref(false)
const showAddHttpServerDialog = ref(false)

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

    // 验证文件类型
    const allowedTypes = ['application/json', 'text/yaml', 'application/x-yaml', 'text/x-yaml']
    if (!allowedTypes.some(type => importForm.value.file!.type.includes(type))
      && !importForm.value.file!.name.match(/\.(json|yaml|yml)$/i)) {
      ElMessage.error('请选择有效的 OpenAPI 文件格式 (.json, .yaml, .yml)')
      return
    }

    // 验证文件大小 (5MB限制)
    if (importForm.value.file!.size > 5 * 1024 * 1024) {
      ElMessage.error('文件大小不能超过 5MB')
      return
    }

    ElMessage.info('正在导入 OpenAPI 文档...')

    // 调用后端 API 导入 OpenAPI 文档
    // 转换为后端API期望的格式
    const apiData: BodyImportOpenapiApiV1OpenapiOpenapiImportPost = {
      file: importForm.value.file as File, // File 继承自 Blob，类型兼容
    }

    const response = await importOpenapiApiV1OpenapiOpenapiImportPost(apiData)

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
function handleUploadChange(uploadFile: any, uploadFiles: any[]) {
  // 确保只保留最新的文件
  if (uploadFiles.length > 1) {
    uploadFiles.splice(0, uploadFiles.length - 1)
  }

  // 从 Element Plus 的 uploadFile 对象中获取原始文件
  const file = uploadFile.raw || uploadFile

  if (file instanceof File) {
    importForm.value.file = file
  }
  else {
    importForm.value.file = null
  }
}

// 文件移除处理
function handleUploadRemove() {
  importForm.value.file = null
}

// 重置导入表单
function resetImportForm() {
  importForm.value = {
    file: null,
  }
  // 清理upload组件状态
  uploadRef.value?.clearFiles()
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

// 新增：服务器管理函数
function addServer() {
  editingServerIndex.value = -1
  newServer.value = {
    name: '',
    description: '',
    type: McpServerType.stdio,
    command: '',
    args: [],
    url: '',
    policy: Policy.on_demand,
    preinstalled: false,
  }
  showAddServerDialog.value = true
}

function editServer(index: number) {
  editingServerIndex.value = index
  newServer.value = { ...configForm.value.servers[index] }
  showAddServerDialog.value = true
}

function saveServer() {
  if (editingServerIndex.value === -1) {
    configForm.value.servers.push({ ...newServer.value })
  }
  else {
    configForm.value.servers[editingServerIndex.value] = { ...newServer.value }
  }
  showAddServerDialog.value = false
}

function deleteServer(index: number) {
  configForm.value.servers.splice(index, 1)
}

// 新增：路由器管理函数
function addRouter() {
  editingRouterIndex.value = -1
  newRouter.value = {
    prefix: '',
    server: '',
    sse_prefix: '',
    cors: null,
  }
  showAddRouterDialog.value = true
}

function editRouter(index: number) {
  editingRouterIndex.value = index
  newRouter.value = { ...configForm.value.routers[index] }
  showAddRouterDialog.value = true
}

function saveRouter() {
  if (editingRouterIndex.value === -1) {
    configForm.value.routers.push({ ...newRouter.value })
  }
  else {
    configForm.value.routers[editingRouterIndex.value] = { ...newRouter.value }
  }
  showAddRouterDialog.value = false
}

function deleteRouter(index: number) {
  configForm.value.routers.splice(index, 1)
}

// 新增：工具管理函数
function addTool() {
  editingToolIndex.value = -1
  newTool.value = {
    name: '',
    description: '',
    method: 'GET',
    path: '',
    args: [],
    headers: {},
    input_schema: {},
    request_body: '',
    response_body: '',
  }
  showAddToolDialog.value = true
}

function editTool(index: number) {
  editingToolIndex.value = index
  newTool.value = { ...configForm.value.tools[index] }
  showAddToolDialog.value = true
}

function saveTool() {
  if (editingToolIndex.value === -1) {
    configForm.value.tools.push({ ...newTool.value })
  }
  else {
    configForm.value.tools[editingToolIndex.value] = { ...newTool.value }
  }
  showAddToolDialog.value = false
}

function deleteTool(index: number) {
  configForm.value.tools.splice(index, 1)
}

// 新增：HTTP服务器管理函数
function addHttpServer() {
  editingHttpServerIndex.value = -1
  newHttpServer.value = {
    name: '',
    description: '',
    url: '',
    tools: [],
  }
  showAddHttpServerDialog.value = true
}

function editHttpServer(index: number) {
  editingHttpServerIndex.value = index
  newHttpServer.value = { ...configForm.value.http_servers[index] }
  showAddHttpServerDialog.value = true
}

function saveHttpServer() {
  if (editingHttpServerIndex.value === -1) {
    configForm.value.http_servers.push({ ...newHttpServer.value })
  }
  else {
    configForm.value.http_servers[editingHttpServerIndex.value] = { ...newHttpServer.value }
  }
  showAddHttpServerDialog.value = false
}

function deleteHttpServer(index: number) {
  configForm.value.http_servers.splice(index, 1)
}

// 新增：数组字段操作函数
function addArgToServer() {
  newServer.value.args.push('')
}

function removeArgFromServer(index: number) {
  newServer.value.args.splice(index, 1)
}

function addToolToHttpServer() {
  newHttpServer.value.tools.push('')
}

function removeToolFromHttpServer(index: number) {
  newHttpServer.value.tools.splice(index, 1)
}

// 修改重置表单函数
function resetForm() {
  editMode.value = false
  activeTab.value = 'basic' // 重置到基本信息选项卡
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
  <div class="page-container p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold mb-2">
        网关配置管理
      </h1>
      <p>
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
      @close="resetImportForm"
    >
      <el-form :model="importForm">
        <el-form-item>
          <el-card class="upload-card" shadow="never">
            <div class="upload-area">
              <el-upload
                ref="uploadRef"
                drag
                :auto-upload="false"
                :show-file-list="true"
                :limit="1"
                accept=".json,.yaml,.yml"
                :on-change="handleUploadChange"
                :on-remove="handleUploadRemove"
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
          <el-button @click="showImportDialog = false; resetImportForm()">取消</el-button>
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
      width="1000px"
      :close-on-click-modal="false"
      @close="resetForm"
    >
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息选项卡 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form :model="configForm" :rules="formRules" label-width="100px">
            <el-form-item label="配置名称" prop="name" required>
              <el-input v-model="configForm.name" placeholder="请输入配置名称" />
            </el-form-item>
            <el-form-item label="租户名称" prop="tenant_name" required>
              <el-select
                v-model="configForm.tenant_name"
                placeholder="请选择租户"
                :loading="tenantLoading"
                :disabled="editMode"
                clearable
                filterable
                style="width: 100%"
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
        </el-tab-pane>

        <!-- MCP服务器选项卡 -->
        <el-tab-pane label="MCP服务器" name="servers">
          <div class="mb-4">
            <el-button type="primary" @click="addServer">
              <Plus />
              添加服务器
            </el-button>
          </div>

          <el-table :data="configForm.servers" stripe style="width: 100%">
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column prop="description" label="描述" width="150" show-overflow-tooltip />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag :type="row.type === 'stdio' ? 'primary' : 'success'">
                  {{ row.type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="command" label="命令" width="120" show-overflow-tooltip />
            <el-table-column prop="policy" label="策略" width="100">
              <template #default="{ row }">
                <el-tag :type="row.policy === 'on_start' ? 'warning' : 'info'">
                  {{ row.policy }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ $index }">
                <div class="flex gap-2">
                  <el-button size="small" type="primary" plain @click="editServer($index)">
                    <Edit class="mr-1" />
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" plain @click="deleteServer($index)">
                    <Delete class="mr-1" />
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 路由器选项卡 -->
        <el-tab-pane label="路由器" name="routers">
          <div class="mb-4">
            <el-button type="primary" @click="addRouter">
              <Plus />
              添加路由器
            </el-button>
          </div>

          <el-table :data="configForm.routers" stripe style="width: 100%">
            <el-table-column prop="prefix" label="前缀" width="150" />
            <el-table-column prop="server" label="服务器" width="150" />
            <el-table-column prop="sse_prefix" label="SSE前缀" width="150" />
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ $index }">
                <div class="flex gap-2">
                  <el-button size="small" type="primary" plain @click="editRouter($index)">
                    <Edit class="mr-1" />
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" plain @click="deleteRouter($index)">
                    <Delete class="mr-1" />
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 工具选项卡 -->
        <el-tab-pane label="工具" name="tools">
          <div class="mb-4">
            <el-button type="primary" @click="addTool">
              <Plus />
              添加工具
            </el-button>
          </div>

          <el-table :data="configForm.tools" stripe style="width: 100%">
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column prop="description" label="描述" width="150" show-overflow-tooltip />
            <el-table-column prop="method" label="方法" width="80">
              <template #default="{ row }">
                <el-tag :type="row.method === 'GET' ? 'success' : row.method === 'POST' ? 'primary' : 'warning'">
                  {{ row.method }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径" width="150" show-overflow-tooltip />
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ $index }">
                <div class="flex gap-2">
                  <el-button size="small" type="primary" plain @click="editTool($index)">
                    <Edit class="mr-1" />
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" plain @click="deleteTool($index)">
                    <Delete class="mr-1" />
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- HTTP服务器选项卡 -->
        <el-tab-pane label="HTTP服务器" name="http_servers">
          <div class="mb-4">
            <el-button type="primary" @click="addHttpServer">
              <Plus />
              添加HTTP服务器
            </el-button>
          </div>

          <el-table :data="configForm.http_servers" stripe style="width: 100%">
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="description" label="描述" width="200" show-overflow-tooltip />
            <el-table-column prop="url" label="URL" width="200" show-overflow-tooltip />
            <el-table-column label="工具数量" width="100">
              <template #default="{ row }">
                <el-tag>{{ row.tools?.length || 0 }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ $index }">
                <div class="flex gap-2">
                  <el-button size="small" type="primary" plain @click="editHttpServer($index)">
                    <Edit class="mr-1" />
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" plain @click="deleteHttpServer($index)">
                    <Delete class="mr-1" />
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false; resetForm()">取消</el-button>
          <el-button type="primary" @click="saveConfig">
            {{ editMode ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- MCP服务器添加/编辑对话框 -->
    <el-dialog
      v-model="showAddServerDialog"
      :title="editingServerIndex === -1 ? '添加服务器' : '编辑服务器'"
      width="600px"
    >
      <el-form :model="newServer" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="newServer.name" placeholder="请输入服务器名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newServer.description" placeholder="请输入服务器描述" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="newServer.type" style="width: 100%">
            <el-option label="stdio" value="stdio" />
            <el-option label="sse" value="sse" />
          </el-select>
        </el-form-item>
        <el-form-item label="命令">
          <el-input v-model="newServer.command" placeholder="请输入执行命令" />
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="newServer.url" placeholder="请输入服务器URL" />
        </el-form-item>
        <el-form-item label="策略">
          <el-select v-model="newServer.policy" style="width: 100%">
            <el-option label="on_demand" value="on_demand" />
            <el-option label="on_start" value="on_start" />
          </el-select>
        </el-form-item>
        <el-form-item label="预安装">
          <el-switch v-model="newServer.preinstalled" />
        </el-form-item>
        <el-form-item label="参数">
          <div class="w-full">
            <div v-for="(arg, index) in newServer.args" :key="index" class="flex mb-2">
              <el-input v-model="newServer.args[index]" placeholder="参数值" />
              <el-button
                type="danger"
                size="small"
                class="ml-2"
                @click="removeArgFromServer(index)"
              >
                删除
              </el-button>
            </div>
            <el-button type="primary" size="small" @click="addArgToServer">
              添加参数
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddServerDialog = false">取消</el-button>
          <el-button type="primary" @click="saveServer">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 路由器添加/编辑对话框 -->
    <el-dialog
      v-model="showAddRouterDialog"
      :title="editingRouterIndex === -1 ? '添加路由器' : '编辑路由器'"
      width="500px"
    >
      <el-form :model="newRouter" label-width="100px">
        <el-form-item label="前缀" required>
          <el-input v-model="newRouter.prefix" placeholder="请输入路由前缀" />
        </el-form-item>
        <el-form-item label="服务器" required>
          <el-input v-model="newRouter.server" placeholder="请输入服务器名称" />
        </el-form-item>
        <el-form-item label="SSE前缀">
          <el-input v-model="newRouter.sse_prefix" placeholder="请输入SSE前缀" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddRouterDialog = false">取消</el-button>
          <el-button type="primary" @click="saveRouter">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 工具添加/编辑对话框 -->
    <el-dialog
      v-model="showAddToolDialog"
      :title="editingToolIndex === -1 ? '添加工具' : '编辑工具'"
      width="700px"
    >
      <el-form :model="newTool" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="newTool.name" placeholder="请输入工具名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newTool.description" placeholder="请输入工具描述" />
        </el-form-item>
        <el-form-item label="HTTP方法" required>
          <el-select v-model="newTool.method" style="width: 100%">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>
        <el-form-item label="路径" required>
          <el-input v-model="newTool.path" placeholder="请输入API路径" />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input
            v-model="newTool.request_body"
            type="textarea"
            :rows="3"
            placeholder="请输入请求体（JSON格式）"
          />
        </el-form-item>
        <el-form-item label="响应体">
          <el-input
            v-model="newTool.response_body"
            type="textarea"
            :rows="3"
            placeholder="请输入响应体（JSON格式）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddToolDialog = false">取消</el-button>
          <el-button type="primary" @click="saveTool">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- HTTP服务器添加/编辑对话框 -->
    <el-dialog
      v-model="showAddHttpServerDialog"
      :title="editingHttpServerIndex === -1 ? '添加HTTP服务器' : '编辑HTTP服务器'"
      width="600px"
    >
      <el-form :model="newHttpServer" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="newHttpServer.name" placeholder="请输入服务器名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newHttpServer.description" placeholder="请输入服务器描述" />
        </el-form-item>
        <el-form-item label="URL" required>
          <el-input v-model="newHttpServer.url" placeholder="请输入服务器URL" />
        </el-form-item>
        <el-form-item label="工具列表">
          <div class="w-full">
            <div v-for="(tool, index) in newHttpServer.tools" :key="index" class="flex mb-2">
              <el-input v-model="newHttpServer.tools[index]" placeholder="工具名称" />
              <el-button
                type="danger"
                size="small"
                class="ml-2"
                @click="removeToolFromHttpServer(index)"
              >
                删除
              </el-button>
            </div>
            <el-button type="primary" size="small" @click="addToolToHttpServer">
              添加工具
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddHttpServerDialog = false">取消</el-button>
          <el-button type="primary" @click="saveHttpServer">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* 仅保留组件特有样式 */

/* 上传卡片样式 */
.upload-card {
  border: 2px dashed var(--el-border-color-light);
  background-color: var(--el-fill-color-extra-light);
  transition: all 0.3s ease;
}

html.dark .upload-card {
  border-color: var(--el-border-color);
  background-color: var(--el-fill-color);
}

.upload-card:hover {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

html.dark .upload-card:hover {
  border-color: var(--el-color-primary);
  background-color: rgba(64, 158, 255, 0.1);
}

.upload-area {
  padding: 20px;
  text-align: center;
}

/* 配置表格特有样式 */
.config-table {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: var(--el-box-shadow-lighter);
}

/* 添加按钮样式 */
.add-item-btn {
  width: 100%;
  height: 60px;
  border: 2px dashed var(--el-border-color-light);
  background-color: var(--el-fill-color-extra-light);
  color: var(--el-text-color-secondary);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.add-item-btn:hover {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

html.dark .add-item-btn {
  border-color: var(--el-border-color);
  background-color: var(--el-fill-color);
}

html.dark .add-item-btn:hover {
  border-color: var(--el-color-primary);
  background-color: rgba(64, 158, 255, 0.1);
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .mb-6 {
    margin-bottom: 16px;
  }

  .flex.gap-2 {
    flex-direction: column;
    gap: 4px;
  }

  .flex.gap-2 .el-button {
    width: 100%;
    margin: 0;
  }
}
</style>
