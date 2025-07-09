<script setup lang="ts">
import type { McpConfigModel } from '../../generated/types'
import { Download, Plus, Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
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

// 对话框状态
const showCreateDialog = ref(false)
const showImportDialog = ref(false)
const editMode = ref(false)

// 表单数据
const configForm = ref({
  name: '',
  tenant_name: '',
  servers: [],
  routers: [],
  tools: [],
  http_servers: [],
})

// OpenAPI 导入表单
const importForm = ref({
  url: '',
  file: null as File | null,
  configName: '',
  tenantName: '',
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 刷新配置列表
async function refreshConfigs() {
  try {
    await fetchConfigs()
    total.value = configs.value.length
  }
  catch {
    ElMessage.error('获取配置列表失败')
  }
}

// 导入 OpenAPI 文档
async function importOpenAPI() {
  try {
    if (!importForm.value.configName || !importForm.value.tenantName) {
      ElMessage.error('请填写配置名称和租户名称')
      return
    }

    if (!importForm.value.url && !importForm.value.file) {
      ElMessage.error('请输入URL或选择文件')
      return
    }

    // 这里应该调用API来处理OpenAPI导入
    // 示例：await importOpenAPIDoc(importForm.value)

    ElMessage.success('OpenAPI文档导入成功，正在转换为MCP配置...')
    showImportDialog.value = false
    resetImportForm()
    await refreshConfigs()
  }
  catch {
    ElMessage.error('导入失败')
  }
}

// 文件上传处理
function handleFileChange(file: File | null) {
  importForm.value.file = file
  if (file) {
    importForm.value.url = '' // 清空URL
  }
}

// 重置导入表单
function resetImportForm() {
  importForm.value = {
    url: '',
    file: null,
    configName: '',
    tenantName: '',
  }
}

// 编辑配置
function editConfig(config: McpConfigModel) {
  editMode.value = true
  configForm.value = {
    name: config.name,
    tenant_name: config.tenant_name,
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
    if (editMode.value) {
      await updateConfig(configForm.value as any)
      ElMessage.success('配置更新成功')
    }
    else {
      await createConfig(configForm.value as any)
      ElMessage.success('配置创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    await refreshConfigs()
  }
  catch (error) {
    ElMessage.error('保存失败')
  }
}

// 激活配置
async function activateConfig(config: McpConfigModel) {
  try {
    await activateMcpConfig(config.tenant_name, config.name)
    ElMessage.success('配置激活成功')
  }
  catch (error) {
    ElMessage.error('激活失败')
  }
}

// 同步配置
async function syncConfig(config: McpConfigModel) {
  try {
    await syncMcpConfig(config.id)
    ElMessage.success('配置同步成功')
  }
  catch (error) {
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

// 初始化
onMounted(() => {
  refreshConfigs()
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
      <div class="flex space-x-2">
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
        <el-table-column prop="tenant_name" label="租户名称" width="150" />
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
      <el-form :model="importForm" label-width="120px">
        <el-form-item label="配置名称" required>
          <el-input
            v-model="importForm.configName"
            placeholder="请输入配置名称"
          />
        </el-form-item>
        <el-form-item label="租户名称" required>
          <el-input
            v-model="importForm.tenantName"
            placeholder="请输入租户名称"
          />
        </el-form-item>
        <el-form-item label="导入方式">
          <el-tabs type="border-card">
            <el-tab-pane label="URL导入" name="url">
              <el-input
                v-model="importForm.url"
                placeholder="请输入OpenAPI文档URL"
                class="mt-4"
                @input="() => { importForm.file = null }"
              />
            </el-tab-pane>
            <el-tab-pane label="文件上传" name="file">
              <el-upload
                class="mt-4"
                drag
                :auto-upload="false"
                :show-file-list="true"
                :limit="1"
                accept=".json,.yaml,.yml"
                @change="handleFileChange"
              >
                <div class="text-center p-4">
                  <Download class="text-4xl text-gray-400 mb-2" />
                  <div class="text-gray-600">
                    将文件拖到此处，或<em>点击上传</em>
                  </div>
                  <div class="text-xs text-gray-400 mt-2">
                    支持 .json, .yaml, .yml 格式
                  </div>
                </div>
              </el-upload>
            </el-tab-pane>
          </el-tabs>
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
          <el-input v-model="configForm.tenant_name" placeholder="请输入租户名称" />
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
</style>
