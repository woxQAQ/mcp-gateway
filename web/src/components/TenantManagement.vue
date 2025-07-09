<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Delete, Edit, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import type { TenantCreate, TenantModel, TenantUpdate } from '../../generated/types'
import {
  createTenantApiV1TenantTenantsPost,
  deleteTenantApiV1TenantTenantsTenantIdDelete,
  listTenantsApiV1TenantTenantsGet,
  updateTenantApiV1TenantTenantsTenantIdPut,
  updateTenantStatusApiV1TenantTenantsTenantIdStatusPatch,
} from '../../generated/api/APIServer.gen'

// 租户数据接口 - 基于API返回的TenantModel
interface Tenant extends TenantModel {
  // 可以添加UI专用的扩展字段
}

// 表单数据
const tenantForm = ref({
  name: '',
  prefix: '',
  description: '',
  is_active: true,
})

// 状态
const tenants = ref<Tenant[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const editMode = ref(false)
const currentTenant = ref<Tenant | null>(null)
const searchKeyword = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 状态选项
const statusOptions = [
  { label: '活跃', value: true },
  { label: '禁用', value: false },
]

// 获取租户列表
async function fetchTenants() {
  loading.value = true
  try {
    const response = await listTenantsApiV1TenantTenantsGet({
      include_inactive: true,
    })

    if (response.status === 200) {
      tenants.value = response.data.tenants
      total.value = response.data.total
    }
    else {
      ElMessage.error('获取租户列表失败')
    }
  }
  catch (error) {
    console.error('获取租户列表失败:', error)
    ElMessage.error('获取租户列表失败')
  }
  finally {
    loading.value = false
  }
}

// 新建租户
function createTenant() {
  editMode.value = false
  currentTenant.value = null
  resetForm()
  showCreateDialog.value = true
}

// 编辑租户
function editTenant(tenant: Tenant) {
  editMode.value = true
  currentTenant.value = tenant
  tenantForm.value = {
    name: tenant.name,
    prefix: tenant.prefix || '',
    description: tenant.description || '',
    is_active: tenant.is_active,
  }
  showCreateDialog.value = true
}

// 保存租户
async function saveTenant() {
  try {
    if (editMode.value && currentTenant.value) {
      // 更新租户逻辑
      const updateData: TenantUpdate = {
        name: tenantForm.value.name,
        prefix: tenantForm.value.prefix || null,
        description: tenantForm.value.description || null,
        is_active: tenantForm.value.is_active,
      }

      const response = await updateTenantApiV1TenantTenantsTenantIdPut(
        currentTenant.value.id,
        updateData,
      )

      if (response.status === 200) {
        ElMessage.success('租户更新成功')
      }
      else {
        ElMessage.error('租户更新失败')
      }
    }
    else {
      // 创建租户逻辑
      const createData: TenantCreate = {
        name: tenantForm.value.name,
        prefix: tenantForm.value.prefix || null,
        description: tenantForm.value.description || null,
      }

      const response = await createTenantApiV1TenantTenantsPost(createData)

      if (response.status === 200) {
        ElMessage.success('租户创建成功')
      }
      else {
        ElMessage.error('租户创建失败')
      }
    }

    showCreateDialog.value = false
    resetForm()
    await fetchTenants()
  }
  catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

// 删除租户
async function deleteTenant(tenant: Tenant) {
  try {
    await ElMessageBox.confirm(
      `确定要删除租户 "${tenant.name}" 吗？这将删除该租户下的所有数据！`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    const response = await deleteTenantApiV1TenantTenantsTenantIdDelete(tenant.id)

    if (response.status === 200) {
      ElMessage.success('租户删除成功')
      await fetchTenants()
    }
    else {
      ElMessage.error('删除失败')
    }
  }
  catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 切换租户状态
async function toggleTenantStatus(tenant: Tenant) {
  try {
    const newStatus = !tenant.is_active
    const response = await updateTenantStatusApiV1TenantTenantsTenantIdStatusPatch(
      tenant.id,
      { is_active: newStatus },
    )

    if (response.status === 200) {
      tenant.is_active = newStatus
      ElMessage.success(`租户状态已${newStatus ? '启用' : '禁用'}`)
    }
    else {
      ElMessage.error('状态更新失败')
    }
  }
  catch (error) {
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败')
  }
}

// 重置表单
function resetForm() {
  tenantForm.value = {
    name: '',
    prefix: '',
    description: '',
    is_active: true,
  }
}

// 搜索租户
function searchTenants() {
  // 实现搜索逻辑
  fetchTenants()
}

// 分页处理
function handleSizeChange(val: number) {
  pageSize.value = val
  fetchTenants()
}

function handleCurrentChange(val: number) {
  currentPage.value = val
  fetchTenants()
}

// 格式化时间
function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

// 获取状态类型
function getStatusType(isActive: boolean) {
  return isActive ? 'success' : 'warning'
}

// 初始化
onMounted(() => {
  fetchTenants()
})
</script>

<template>
  <div class="tenant-management-container p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        租户管理
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        管理平台租户配置、资源分配和访问控制
      </p>
    </div>

    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div class="flex items-center space-x-4">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索租户名称或前缀"
          class="w-80"
          @keyup.enter="searchTenants"
        >
          <template #prefix>
            <Search />
          </template>
        </el-input>
        <el-button @click="searchTenants">
          搜索
        </el-button>
      </div>

      <div class="flex space-x-2">
        <el-button @click="fetchTenants">
          <Refresh />
          刷新
        </el-button>
        <el-button type="primary" @click="createTenant">
          <Plus />
          新建租户
        </el-button>
      </div>
    </div>

    <!-- 租户列表 -->
    <el-card class="shadow-md">
      <el-table
        v-loading="loading"
        :data="tenants"
        style="width: 100%"
        stripe
        class="tenant-table"
      >
        <el-table-column prop="name" label="租户名称" width="200" />
        <el-table-column prop="prefix" label="前缀" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.is_active)">
              {{ row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="gmt_created" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.gmt_created) }}
          </template>
        </el-table-column>
        <el-table-column prop="gmt_updated" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.gmt_updated) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="editTenant(row)"
            >
              <Edit />
              编辑
            </el-button>
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              size="small"
              @click="toggleTenantStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteTenant(row)"
            >
              <Delete />
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="mt-4 flex justify-center">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑租户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editMode ? '编辑租户' : '新建租户'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="tenantForm" label-width="100px">
        <el-form-item label="租户名称" required>
          <el-input v-model="tenantForm.name" placeholder="请输入租户名称" />
        </el-form-item>
        <el-form-item label="前缀">
          <el-input v-model="tenantForm.prefix" placeholder="请输入租户前缀（可选）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="tenantForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入租户描述信息"
          />
        </el-form-item>
        <el-form-item v-if="editMode" label="状态" required>
          <el-select v-model="tenantForm.is_active" placeholder="请选择状态">
            <el-option
              v-for="option in statusOptions"
              :key="String(option.value)"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveTenant">
            {{ editMode ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tenant-management-container {
  background: #f8fafc;
  min-height: 100vh;
}

.tenant-table {
  background: white;
  border-radius: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.el-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.el-button {
  border-radius: 6px;
}

.el-input {
  border-radius: 6px;
}

.el-select {
  width: 100%;
}

.el-pagination {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .tenant-management-container {
    padding: 16px;
  }

  .mb-6 {
    margin-bottom: 16px;
  }

  .el-table-column {
    min-width: 120px;
  }
}
</style>
