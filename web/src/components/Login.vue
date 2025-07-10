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
function validateConfirmPassword(_: any, value: any, callback: any) {
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
  position: relative;
}

/* 暗色模式下的背景渐变 */
html.dark .login-container {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}

.login-card {
  width: 400px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  overflow: hidden;
}

/* 暗色模式下的卡片样式 */
html.dark .login-card {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  background-color: rgba(29, 30, 31, 0.95);
  border-color: var(--el-border-color-light);
}

.card-header {
  text-align: center;
  padding: 20px 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

/* 暗色模式下的卡片头部 */
html.dark .card-header {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
  border-bottom-color: var(--el-border-color-light);
}

.title {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-text-color-primary);
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 暗色模式下的标题 */
html.dark .title {
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 表单容器 */
.login-card :deep(.el-card__body) {
  padding: 32px;
  background-color: var(--el-bg-color);
}

/* 表单项样式 */
.login-card :deep(.el-form-item) {
  margin-bottom: 24px;
}

.login-card :deep(.el-form-item__label) {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

/* 输入框样式增强 */
.login-card :deep(.el-input) {
  height: 44px;
}

.login-card :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
  background-color: var(--el-fill-color-light);
  box-shadow: 0 0 0 1px var(--el-border-color-lighter) inset;
}

.login-card :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
  transform: translateY(-1px);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 2px var(--el-color-primary-light-8) inset,
    0 0 0 1px var(--el-color-primary) inset;
  transform: translateY(-1px);
}

/* 暗色模式下的输入框 */
html.dark .login-card :deep(.el-input__wrapper) {
  background-color: rgba(38, 39, 39, 0.8);
  backdrop-filter: blur(8px);
}

html.dark .login-card :deep(.el-input__wrapper:hover) {
  background-color: rgba(48, 49, 51, 0.9);
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-dark-2) 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
}

.login-button:active {
  transform: translateY(0);
}

/* 暗色模式下的登录按钮 */
html.dark .login-button {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #2b6bb2 100%);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

html.dark .login-button:hover {
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.3);
}

.error-message {
  margin-bottom: 20px;
}

.error-message :deep(.el-alert) {
  border-radius: 8px;
  background-color: var(--el-color-danger-light-9);
  border-color: var(--el-color-danger-light-7);
}

/* 暗色模式下的错误提示 */
html.dark .error-message :deep(.el-alert) {
  background-color: rgba(196, 86, 86, 0.1);
  border-color: var(--el-color-danger-light-7);
}

.toggle-button {
  width: 100%;
  color: var(--el-color-primary);
  text-decoration: none;
  font-size: 14px;
  padding: 12px 0;
  border-radius: 8px;
  background-color: transparent;
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.3s ease;
}

.toggle-button:hover {
  color: var(--el-color-primary-light-3);
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
  transform: translateY(-1px);
}

/* 暗色模式下的切换按钮 */
html.dark .toggle-button {
  border-color: var(--el-border-color-light);
  color: var(--el-color-primary-light-3);
}

html.dark .toggle-button:hover {
  background-color: rgba(64, 158, 255, 0.1);
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    width: 90%;
    margin: 0 20px;
  }

  .login-card :deep(.el-card__body) {
    padding: 24px;
  }

  .title {
    font-size: 20px;
  }
}

/* 动画效果 */
.login-card {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 加载状态下的按钮样式 */
.login-button.is-loading {
  pointer-events: none;
}

.login-button.is-loading :deep(.el-icon) {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
