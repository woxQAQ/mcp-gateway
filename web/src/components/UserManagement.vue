<script setup lang="ts">
import type { UserModel } from '../../generated/types/UserModel'
import { Delete, Edit, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useUsers } from '../stores/users'

// 使用用户状态管理
const {
  loading,
  error,
  fetchUsers,
  createUser,
  deleteUser,
  updateUserStatus,
  searchUsers,
  clearError,
} = useUsers()

// 表单数据
const userForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'normal',
})

// 状态
const showCreateDialog = ref(false)
const editMode = ref(false)
const currentUser = ref<UserModel | null>(null)
const searchKeyword = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 计算属性 - 过滤和分页的用户列表
const filteredUsers = computed(() => {
  return searchUsers(searchKeyword.value)
})

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredUsers.value.slice(start, end)
})

const total = computed(() => filteredUsers.value.length)

// 角色选项
const roleOptions = [
  { label: '管理员', value: 'admin' },
  { label: '普通用户', value: 'normal' },
]

// 状态选项 (暂未使用，保留以备将来使用)
// const statusOptions = [
//   { label: '活跃', value: true },
//   { label: '禁用', value: false },
// ]

// 新建用户
function createNewUser() {
  editMode.value = false
  currentUser.value = null
  resetForm()
  showCreateDialog.value = true
}

// 编辑用户
function editUser(user: UserModel) {
  editMode.value = true
  currentUser.value = user
  userForm.value = {
    username: user.username,
    email: user.email || '',
    password: '',
    confirmPassword: '',
    role: user.role,
  }
  showCreateDialog.value = true
}

// 保存用户
async function saveUser() {
  try {
    if (editMode.value) {
      // 更新用户逻辑 - 后端暂无此API
      ElMessage.warning('编辑用户功能需要后端API支持')
    }
    else {
      // 表单验证
      if (!userForm.value.username.trim()) {
        ElMessage.error('用户名不能为空')
        return
      }
      if (!userForm.value.password) {
        ElMessage.error('密码不能为空')
        return
      }
      if (userForm.value.password !== userForm.value.confirmPassword) {
        ElMessage.error('密码确认不一致')
        return
      }
      if (userForm.value.password.length < 6) {
        ElMessage.error('密码长度至少6位')
        return
      }

      await createUser({
        username: userForm.value.username.trim(),
        email: userForm.value.email?.trim() || undefined,
        password: userForm.value.password,
        confirmPassword: userForm.value.confirmPassword,
      })

      ElMessage.success('用户创建成功')
      showCreateDialog.value = false
      resetForm()
    }
  }
  catch (err: any) {
    console.error('保存用户失败:', err)
    // 错误信息已经在store中设置，不需要额外显示
  }
}

// 删除用户
async function handleDeleteUser(user: UserModel) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    await deleteUser(user.id)
    ElMessage.success('用户删除成功')
  }
  catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      // 错误已经在store中处理
    }
  }
}

// 切换用户状态
async function toggleUserStatus(user: UserModel) {
  try {
    const newStatus = !user.is_active
    const action = newStatus ? '启用' : '禁用'

    // 添加确认对话框
    await ElMessageBox.confirm(
      `确定要${action}用户 "${user.username}" 吗？`,
      `确认${action}`,
      {
        confirmButtonText: action,
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    await updateUserStatus(user, newStatus)
    ElMessage.success(`用户状态已${action}`)
  }
  catch (err: any) {
    if (err !== 'cancel') {
      console.error('状态更新失败:', err)
      // 错误信息已经在store中设置，这里不再重复显示
      if (!getErrorMessage()) {
        ElMessage.error('状态更新失败')
      }
    }
  }
}

// 重置表单
function resetForm() {
  userForm.value = {
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'normal',
  }
}

// 搜索用户
function handleSearch() {
  currentPage.value = 1 // 重置到第一页
}

// 分页处理
function handleSizeChange(val: number) {
  pageSize.value = val
  currentPage.value = 1
}

function handleCurrentChange(val: number) {
  currentPage.value = val
}

// 格式化时间
function formatTime(time?: string) {
  if (!time)
    return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 获取角色标签
function getRoleLabel(role: string) {
  const option = roleOptions.find(r => r.value === role)
  return option ? option.label : role
}

// 处理错误显示
function getErrorMessage() {
  return error.value
}

// 初始化
onMounted(async () => {
  try {
    await fetchUsers()
  }
  catch (err) {
    console.error('初始化用户列表失败:', err)
  }
})
</script>

<template>
  <div class="page-container p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold mb-2">
        用户管理
      </h1>
      <p>
        管理系统用户账户、角色权限和状态设置
      </p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="getErrorMessage()"
      :title="getErrorMessage()"
      type="error"
      class="mb-4"
      show-icon
      closable
      @close="clearError"
    />

    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div class="flex items-center space-x-4">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名或邮箱"
          class="w-80"
          @keyup.enter="handleSearch"
          @input="handleSearch"
        >
          <template #prefix>
            <Search />
          </template>
        </el-input>
      </div>

      <div class="flex space-x-2">
        <el-button :loading="loading" @click="fetchUsers">
          <Refresh />
          刷新
        </el-button>
        <el-button type="primary" @click="createNewUser">
          <Plus />
          新建用户
        </el-button>
      </div>
    </div>

    <!-- 用户列表 -->
    <el-card class="shadow-md fade-in-up">
      <el-table
        v-loading="loading"
        :data="paginatedUsers"
        style="width: 100%"
        stripe
        class="user-table"
      >
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag
              :type="row.role === 'admin' ? 'danger' : 'primary'"
            >
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'warning'">
              {{ row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.date_joined) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              disabled
              title="编辑功能暂未开放"
              @click="editUser(row)"
            >
              <Edit />
              编辑
            </el-button>
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              size="small"
              :loading="loading"
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              type="danger"
              size="small"
              :loading="loading"
              @click="handleDeleteUser(row)"
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

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editMode ? '编辑用户' : '新建用户'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="userForm" label-width="100px">
        <el-form-item label="用户名" required>
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名（2-50个字符）"
            :disabled="editMode"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input
            v-model="userForm.email"
            placeholder="请输入邮箱（可选）"
            type="email"
          />
        </el-form-item>
        <el-form-item :label="editMode ? '新密码' : '密码'" :required="!editMode">
          <el-input
            v-model="userForm.password"
            type="password"
            :placeholder="editMode ? '留空则不修改密码' : '请输入密码（至少6位）'"
            show-password
          />
        </el-form-item>
        <el-form-item
          v-if="!editMode"
          label="确认密码"
          required
        >
          <el-input
            v-model="userForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option
              v-for="option in roleOptions"
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
          <el-button
            type="primary"
            :loading="loading"
            @click="saveUser"
          >
            {{ editMode ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* 仅保留组件特定样式 */
.user-table {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: var(--el-box-shadow-lighter);
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .mb-6 {
    margin-bottom: 16px;
  }

  .flex.space-x-2 {
    flex-direction: column;
    gap: 8px;
  }

  .flex.space-x-2 .el-button {
    width: 100%;
    margin: 0;
  }
}
</style>
