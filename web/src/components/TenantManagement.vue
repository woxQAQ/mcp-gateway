<script setup lang="ts">
import { Delete, Edit, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

// 租户数据接口
interface Tenant {
  id: string
  name: string
  domain: string
  description: string
  status: 'active' | 'inactive' | 'suspended'
  created_at: string
  user_count: number
  config_count: number
}

// 表单数据
const tenantForm = ref({
  name: '',
  domain: '',
  description: '',
  status: 'active',
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
  { label: '活跃', value: 'active' },
  { label: '禁用', value: 'inactive' },
  { label: '暂停', value: 'suspended' },
]

// 获取租户列表
async function fetchTenants() {
  loading.value = true
  try {
    // 模拟数据，实际应该调用API
    tenants.value = [
      {
        id: '1',
        name: '默认租户',
        domain: 'default.example.com',
        description: '系统默认租户',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        user_count: 10,
        config_count: 5,
      },
      {
        id: '2',
        name: '企业租户A',
        domain: 'companya.example.com',
        description: '企业A的专用租户',
        status: 'active',
        created_at: '2024-01-02T00:00:00Z',
        user_count: 25,
        config_count: 12,
      },
      {
        id: '3',
        name: '企业租户B',
        domain: 'companyb.example.com',
        description: '企业B的专用租户',
        status: 'suspended',
        created_at: '2024-01-03T00:00:00Z',
        user_count: 15,
        config_count: 8,
      },
    ]
    total.value = tenants.value.length
  }
  catch {
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
    domain: tenant.domain,
    description: tenant.description,
    status: tenant.status,
  }
  showCreateDialog.value = true
}

// 保存租户
async function saveTenant() {
  try {
    if (editMode.value) {
      // 更新租户逻辑
      ElMessage.success('租户更新成功')
    }
    else {
      // 创建租户逻辑
      ElMessage.success('租户创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    await fetchTenants()
  }
  catch {
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

    // 删除租户逻辑
    ElMessage.success('租户删除成功')
    await fetchTenants()
  }
  catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 切换租户状态
async function toggleTenantStatus(tenant: Tenant) {
  try {
    const newStatus = tenant.status === 'active' ? 'inactive' : 'active'
    // 更新状态逻辑
    tenant.status = newStatus
    ElMessage.success(`租户状态已${newStatus === 'active' ? '启用' : '禁用'}`)
  }
  catch {
    ElMessage.error('状态更新失败')
  }
}

// 重置表单
function resetForm() {
  tenantForm.value = {
    name: '',
    domain: '',
    description: '',
    status: 'active',
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
function getStatusType(status: string) {
  switch (status) {
    case 'active':
      return 'success'
    case 'inactive':
      return 'warning'
    case 'suspended':
      return 'danger'
    default:
      return 'info'
  }
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
          placeholder="搜索租户名称或域名"
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
        <el-table-column prop="domain" label="域名" width="250" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ statusOptions.find(s => s.value === row.status)?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_count" label="用户数" width="100">
          <template #default="{ row }">
            <el-tag type="info">
              {{ row.user_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="config_count" label="配置数" width="100">
          <template #default="{ row }">
            <el-tag type="success">
              {{ row.config_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
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
              :type="row.status === 'active' ? 'warning' : 'success'"
              size="small"
              @click="toggleTenantStatus(row)"
            >
              {{ row.status === 'active' ? '禁用' : '启用' }}
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
        <el-form-item label="域名" required>
          <el-input v-model="tenantForm.domain" placeholder="请输入域名，如：tenant.example.com" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="tenantForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入租户描述信息"
          />
        </el-form-item>
        <el-form-item label="状态" required>
          <el-select v-model="tenantForm.status" placeholder="请选择状态">
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
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
</style>
