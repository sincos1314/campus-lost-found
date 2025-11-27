<template>
  <div class="login-container">
    <el-card class="login-card" shadow="always">
      <template #header>
        <div class="card-header">
          <el-icon :size="40" color="#667eea"><UserFilled /></el-icon>
          <h2>用户登录</h2>
        </div>
      </template>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-width="0"
        size="large"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="links">
        <span>还没有账号？</span>
        <el-link type="primary" @click="$router.push('/register')">立即注册</el-link>
        <el-divider direction="vertical" />
        <el-link type="warning" @click="openReset">忘记密码</el-link>
      </div>
    </el-card>
    <el-dialog v-model="resetVisible" title="重置密码" width="500px">
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="resetForm.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="resetForm.email" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="resetForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible=false">取消</el-button>
        <el-button type="primary" :loading="resetLoading" @click="submitReset">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import { setToken, setUser } from '../utils/auth'

const router = useRouter()
const loginFormRef = ref()
const loading = ref(false)
const resetFormRef = ref()
const resetVisible = ref(false)
const resetLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})
const resetForm = reactive({ username: '', email: '', new_password: '', confirm: '' })

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: ['blur','change'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: ['blur','change'] },
    { min: 6, message: '密码长度至少6位', trigger: ['blur','change'] }
  ]
}
const resetRules = {
  username: [{ required: true, message: '请输入用户名', trigger: ['blur','change'] }],
  email: [{ required: true, message: '请输入邮箱', trigger: ['blur','change'] }, { type: 'email', message: '邮箱格式不正确', trigger: ['blur','change'] }],
  new_password: [{ required: true, message: '请输入新密码', trigger: ['blur','change'] }, { min: 6, message: '密码长度至少6位', trigger: ['blur','change'] }],
  confirm: [{ required: true, message: '请确认新密码', trigger: ['blur','change'] }, { validator: (r,v,cb)=>{ v!==resetForm.new_password?cb(new Error('两次密码不一致')):cb() }, trigger: ['blur','change'] }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) { ElMessage.error('请检查用户名与密码'); return }
    
    loading.value = true
    try {
      const data = await request.post('/auth/login', loginForm)
      setToken(data.access_token)
      setUser(data.user)
      ElMessage.success('登录成功！')
      if (data.user?.role === 'admin') {
        router.push('/admin')
      } else {
        router.push('/')
      }
    } catch (error) {
      const msg = error?.response?.data?.message || '登录失败，请重试'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}

const openReset = () => { resetVisible.value = true }
const submitReset = async () => {
  if (!resetFormRef.value) return
  await resetFormRef.value.validate(async (valid) => {
    if (!valid) { ElMessage.error('请检查重置信息'); return }
    resetLoading.value = true
    try {
      await request.post('/auth/reset-password', { username: resetForm.username, email: resetForm.email, new_password: resetForm.new_password })
      ElMessage.success('密码重置成功，请使用新密码登录')
      resetVisible.value = false
      resetForm.username = ''
      resetForm.email = ''
      resetForm.new_password = ''
      resetForm.confirm = ''
    } catch (e) {
      const msg = e?.response?.data?.message || '重置失败'
      ElMessage.error(msg)
    } finally { resetLoading.value = false }
  })
}
</script>

<style scoped>
.login-container {
  min-height: calc(100vh - 130px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  border-radius: 15px;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.card-header h2 {
  margin: 0;
  color: #333;
}

.login-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
}

.links {
  text-align: center;
  color: #666;
}

.links span {
  margin-right: 10px;
}
</style>
