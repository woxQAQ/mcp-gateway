<script setup lang="ts">
import type { McpConfigModel } from '../../generated/types'
import { Plus, Refresh } from '@element-plus/icons-vue'
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
  catch (error) {
    ElMessage.error('获取配置列表失败')
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
  <div class="mcp-config-container">
    <!-- 头部操作栏 -->
    <div class="header-actions">
      <el-button type="primary" @click="showCreateDialog = true">
        <Plus />
        新建配置
      </el-button>
      <el-button @click="refreshConfigs">
        <Refresh />
        刷新
      </el-button>
    </div>

    <!-- 配置列表 -->
    <el-table
      v-loading="loading"
      :data="configs"
      style="width: 100%"
      stripe
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
      <el-table-column label="操作" width="300">
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
    <div class="pagination">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editMode ? '编辑配置' : '新建配置'"
      width="800px"
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
        <el-button @click="showCreateDialog = false">
          取消
        </el-button>
        <el-button type="primary" @click="saveConfig">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.mcp-config-container {
  padding: 20px;
}

.header-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
