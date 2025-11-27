<template>
  <div class="register-container">
    <el-card class="register-card" shadow="always">
      <template #header>
        <div class="card-header">
          <el-icon :size="40" color="#667eea"><Avatar /></el-icon>
          <h2 v-if="identity==='student'">学生注册</h2>
          <h2 v-else-if="identity==='teacher'">教师注册</h2>
          <h2 v-else>选择身份</h2>
        </div>
      </template>

      <div v-if="!identity" class="identity-select">
        <el-select v-model="identity" placeholder="您的身份是：" style="width:100%">
          <el-option label="教师" value="teacher" />
          <el-option label="学生" value="student" />
        </el-select>
        <div style="margin-top:16px; text-align:center">
          <el-button type="primary" :disabled="!identity">下一步</el-button>
        </div>
      </div>

      <el-form v-else
        ref="registerFormRef"
        :model="registerForm"
        :rules="rules"
        label-width="80px"
        size="large"
      >
        <template v-if="identity==='teacher'">
          <el-form-item label="工号" prop="staff_id">
            <el-input v-model="registerForm.staff_id" placeholder="请输入工号" />
          </el-form-item>
        </template>
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="registerForm.phone"
            placeholder="请输入手机号"
            prefix-icon="Phone"
          />
        </el-form-item>

        <template v-if="identity==='student'">
          <el-form-item label="院系" prop="department">
            <el-input v-model="registerForm.department" placeholder="请输入院系" />
          </el-form-item>
          <el-form-item label="年级" prop="grade">
            <el-select v-model="registerForm.grade" placeholder="请选择年级">
              <el-option label="大一" value="大一" />
              <el-option label="大二" value="大二" />
              <el-option label="大三" value="大三" />
              <el-option label="大四" value="大四" />
            </el-select>
          </el-form-item>
          <el-form-item label="班级" prop="class_name">
            <el-input v-model="registerForm.class_name" placeholder="请输入班级" />
          </el-form-item>
          <el-form-item label="学号" prop="student_id">
            <el-input v-model="registerForm.student_id" placeholder="请输入学号" />
          </el-form-item>
          <el-form-item label="性别" prop="gender">
            <el-select v-model="registerForm.gender" placeholder="选择性别(可选)">
              <el-option label="男" value="male" />
              <el-option label="女" value="female" />
              <el-option label="其他" value="other" />
              <el-option label="不透露" value="secret" />
            </el-select>
          </el-form-item>
        </template>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="register-btn"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </el-button>
          <el-button type="primary" link @click="router.push('/login')" style="margin-left:8px">忘记密码</el-button>
        </el-form-item>
      </el-form>

      <div class="links">
        <span>已有账号？</span>
        <el-link type="primary" @click="$router.push('/login')">立即登录</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const registerFormRef = ref()
const loading = ref(false)

const identity = ref('')
const registerForm = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
  department: '',
  grade: '大一',
  class_name: '',
  student_id: '',
  gender: '',
  staff_id: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  staff_id: [
    { required: identity.value==='teacher', message: '请输入工号', trigger: 'blur' }
  ],
  department: [{ required: true, message: '请输入院系', trigger: 'blur' }],
  grade: [{ required: true, message: '请选择年级', trigger: ['blur','change'] }],
  class_name: [{ required: true, message: '请输入班级', trigger: 'blur' }],
  student_id: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await request.post('/auth/register', {
        username: registerForm.username,
        email: registerForm.email,
        phone: registerForm.phone,
        password: registerForm.password,
        department: identity.value==='student' ? registerForm.department : '',
        grade: identity.value==='student' ? registerForm.grade : '',
        class_name: identity.value==='student' ? registerForm.class_name : '',
        student_id: identity.value==='student' ? registerForm.student_id : '',
        gender: identity.value==='student' ? registerForm.gender : '',
        identity: identity.value || 'student',
        staff_id: identity.value==='teacher' ? registerForm.staff_id : ''
      })
      ElMessage.success('注册成功！请登录')
      router.push('/login')
    } catch (error) {
      console.error('注册失败:', error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-container {
  min-height: calc(100vh - 130px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30px 0;
}

.register-card {
  width: 500px;
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

.register-btn {
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
