<script setup lang="ts">
import { Lock, Message, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

// 路由
const router = useRouter()

// 认证store
const { login, register, loading } = useAuth()

// 表单引用
const formRef = ref()

// 模式控制：true为登录，false为注册
const isLoginMode = ref(true)

// 表单数据
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
})

// 确认密码验证函数
function validateConfirmPassword(rule: any, value: any, callback: any) {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  }
  else if (value !== form.password) {
    callback(new Error('两次输入密码不一致!'))
  }
  else {
    callback()
  }
}

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' },
  ],
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' },
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] },
  ],
}

// 当前使用的验证规则
const currentRules = computed(() => isLoginMode.value ? loginRules : registerRules)

// 错误信息
const errorMessage = ref('')

// 切换模式
function toggleMode() {
  isLoginMode.value = !isLoginMode.value
  errorMessage.value = ''
  // 清空表单
  formRef.value?.resetFields()
}

// 处理登录
async function handleLogin() {
  if (!formRef.value)
    return

  try {
    // 验证表单
    await formRef.value.validate()

    // 清除错误信息
    errorMessage.value = ''

    // 执行登录
    await login(form.username, form.password)

    // 登录成功
    ElMessage.success('登录成功')
    router.push('/dashboard')
  }
  catch (error: any) {
    if (error.message) {
      errorMessage.value = error.message
    }
    else {
      errorMessage.value = '登录失败，请检查用户名和密码'
    }
  }
}

// 处理注册
async function handleRegister() {
  if (!formRef.value)
    return

  try {
    // 验证表单
    await formRef.value.validate()

    // 清除错误信息
    errorMessage.value = ''

    // 执行注册
    await register(form.username, form.password, form.confirmPassword, form.email || undefined)

    // 注册成功
    ElMessage.success('注册成功')
    router.push('/dashboard')
  }
  catch (error: any) {
    if (error.message) {
      errorMessage.value = error.message
    }
    else {
      errorMessage.value = '注册失败，请检查输入信息'
    }
  }
}

// 处理提交
function handleSubmit() {
  if (isLoginMode.value) {
    handleLogin()
  }
  else {
    handleRegister()
  }
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{ isLoginMode ? '🔐 用户登录' : '📝 用户注册' }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="currentRules"
        label-width="80px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <!-- 注册模式下的额外字段 -->
        <template v-if="!isLoginMode">
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="form.email"
              type="email"
              placeholder="请输入邮箱（可选）"
              :prefix-icon="Message"
              clearable
            />
          </el-form-item>
        </template>

        <div v-if="errorMessage" class="error-message">
          <el-alert :title="errorMessage" type="error" show-icon />
        </div>

        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ loading ? (isLoginMode ? '登录中...' : '注册中...') : (isLoginMode ? '登录' : '注册') }}
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-button
            type="text"
            class="toggle-button"
            @click="toggleMode"
          >
            {{ isLoginMode ? '没有账号？点击注册' : '已有账号？点击登录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
}

.card-header {
  text-align: center;
}

.title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.login-button {
  width: 100%;
  height: 40px;
  font-size: 16px;
}

.error-message {
  margin-bottom: 20px;
}

.toggle-button {
  width: 100%;
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
}

.toggle-button:hover {
  color: #66b1ff;
}
</style>
