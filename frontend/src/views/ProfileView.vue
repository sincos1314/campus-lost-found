<template>
  <div class="profile-container">
    <el-row :gutter="20">
      <el-col :xs="24" :md="8">
        <el-card class="user-card card-glass hover-rise" shadow="never">
          <div class="user-avatar">
            <el-avatar :size="100" :src="user?.avatar_url ? `http://localhost:5000${user.avatar_url}` : ''">
              <el-icon v-if="!user?.avatar_url" :size="50"><User /></el-icon>
            </el-avatar>
          </div>
          <h2>{{ user?.username }}</h2>
          <p class="join-date">加入于 {{ user?.created_at }}</p>
          <p class="join-date">当前年级：{{ user?.grade_display || user?.grade || '未设置' }}</p>
          <el-upload
            class="avatar-uploader"
            :action="'http://localhost:5000/api/auth/avatar'"
            :headers="{ Authorization: `Bearer ${token}` }"
            name="avatar"
            :show-file-list="false"
            :before-upload="beforeAvatarUpload"
            :on-success="handleAvatarSuccess"
            :on-error="handleAvatarError"
          >
            <button class="avatar-upload-btn">
              {{ user?.avatar_url ? '修改头像' : '上传头像' }}
            </button>
          </el-upload>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16">
        <el-card class="profile-card card-glass" shadow="never">
          <template #header>
            <span>个人资料</span>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            size="large"
          >
            <el-form-item label="用户名">
              <el-input v-model="user.username" disabled />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" />
            </el-form-item>

            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" />
            </el-form-item>

            <el-form-item label="院系">
              <el-input v-model="form.department" />
            </el-form-item>
            <el-form-item label="年级">
              <el-select v-model="form.grade" placeholder="选择年级">
                <el-option label="大一" value="大一" />
                <el-option label="大二" value="大二" />
                <el-option label="大三" value="大三" />
                <el-option label="大四" value="大四" />
              </el-select>
            </el-form-item>
            <el-form-item label="班级">
              <el-input v-model="form.class_name" />
            </el-form-item>
            <el-form-item label="学号">
              <el-input v-model="form.student_id" />
            </el-form-item>
            <el-form-item label="性别">
              <el-select v-model="form.gender" placeholder="选择性别">
                <el-option label="男" value="male" />
                <el-option label="女" value="female" />
                <el-option label="其他" value="other" />
                <el-option label="不透露" value="secret" />
              </el-select>
            </el-form-item>

            <el-divider content-position="left">隐私设置</el-divider>
            <el-form-item label="发布历史可见性">
              <el-radio-group v-model="privacy.visibility_setting">
                <el-radio label="hidden">隐藏</el-radio>
                <el-radio label="partial">部分隐藏</el-radio>
                <el-radio label="public">不隐藏</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="privacy.visibility_setting==='partial'" label="其他人默认">
              <el-select v-model="privacy.others_policy">
                <el-option label="显示" value="show" />
                <el-option label="隐藏" value="hide" />
              </el-select>
              <el-button style="margin-left:10px" @click="openPrivacyRules">设置名单</el-button>
            </el-form-item>

            <el-divider content-position="left">修改密码</el-divider>

            <el-form-item label="新密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="留空则不修改"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="留空则不修改"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleUpdate" :loading="loading">
                保存修改
              </el-button>
              <el-button type="primary" plain @click="savePrivacy">保存隐私设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request, { apiOrigin, absoluteUrl } from '../utils/request'
import { setUser, getToken } from '../utils/auth'

const formRef = ref()
const loading = ref(false)
const user = ref({})
const token = getToken()
const privacy = reactive({ visibility_setting: 'public', others_policy: 'show', rules: [] })
const showList = ref([])
const hideList = ref([])
const conversations = ref([])

const form = reactive({
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
  department: '',
  grade: '',
  class_name: '',
  student_id: '',
  gender: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (form.password && value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validatePhone = (rule, value, callback) => {
  if (!value) return callback()
  const v = String(value).trim()
  const re = /^1[3-9]\d{9}$/
  if (!re.test(v)) {
    callback(new Error('请输入正确的手机号'))
  } else {
    callback()
  }
}

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { validator: validatePhone, trigger: ['blur', 'change'] }
  ],
  password: [
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loadProfile = async () => {
  try {
    user.value = await request.get('/auth/profile')
    setUser(user.value)
    form.email = user.value.email
    form.phone = user.value.phone
    form.department = user.value.department || ''
    form.grade = user.value.grade || ''
    form.class_name = user.value.class_name || ''
    form.student_id = user.value.student_id || ''
    form.gender = user.value.gender || ''
    const p = await request.get('/privacy')
    privacy.visibility_setting = p.visibility_setting
    privacy.others_policy = p.others_policy
    privacy.rules = p.rules
  } catch (error) {
    console.error('加载个人资料失败:', error)
  }
}

const handleUpdate = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const updateData = {
        email: form.email,
        phone: form.phone,
        department: form.department,
        grade: form.grade,
        class_name: form.class_name,
        student_id: form.student_id,
        gender: form.gender
      }
      if (form.password) {
        updateData.password = form.password
      }

      const updatedUser = await request.put('/auth/profile', updateData)
      setUser(updatedUser)
      user.value = updatedUser
      
      form.password = ''
      form.confirmPassword = ''
      
      ElMessage.success('修改成功！')
    } catch (error) {
      console.error('修改失败:', error)
    } finally {
      loading.value = false
    }
  })
}

const openPrivacyRules = async () => {
  conversations.value = await request.get('/conversations')
  const userIdSetShow = privacy.rules.filter(r=>r.rule==='show').map(r=>r.target_user_id)
  const userIdSetHide = privacy.rules.filter(r=>r.rule==='hide').map(r=>r.target_user_id)
  showList.value = userIdSetShow
  hideList.value = userIdSetHide
  ElMessage.info('在“我的发布”页面配置名单更直观，稍后我会在那里也加入入口')
}

const savePrivacy = async () => {
  try {
    await request.put('/privacy', { visibility_setting: privacy.visibility_setting, others_policy: privacy.others_policy })
    await request.put('/privacy/rules', { show_list: showList.value, hide_list: hideList.value })
    ElMessage.success('隐私设置已更新')
  } catch (e) {
    console.error(e)
  }
}

const beforeAvatarUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 <= 10
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过10MB！')
    return false
  }
  return true
}

const handleAvatarSuccess = (res) => {
  setUser(res)
  user.value = res
  ElMessage.success('头像更新成功')
}

const handleAvatarError = () => {
  ElMessage.error('头像上传失败')
}

const router = useRouter()
const goAdmin = () => {
  router.push('/admin')
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.user-card,
.profile-card {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 2rem;
}

.user-card {
  text-align: center;
}

.user-avatar {
  margin-bottom: 20px;
}

.user-card h2 {
  margin: 10px 0;
  color: var(--color-text);
  font-weight: 900;
  font-size: 1.5rem;
}

.join-date {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
}

/* 移除 Element Plus 默认的输入框包装器样式 */
.profile-card :deep(.el-input),
.profile-card :deep(.el-select) {
  border: none !important;
  box-shadow: none !important;
}

.profile-card :deep(.el-input__wrapper),
.profile-card :deep(.el-select__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

.profile-card :deep(.el-input__inner),
.profile-card :deep(.el-select__placeholder),
.profile-card :deep(.el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.profile-card :deep(.el-input__wrapper.is-focus),
.profile-card :deep(.el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.profile-card :deep(.el-form-item__label) {
  font-weight: 700;
  color: var(--color-text);
}

.profile-card :deep(.el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.profile-card :deep(.el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

.profile-card :deep(.el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

/* 修改头像按钮样式 */
.avatar-upload-btn {
  padding: 0.6rem 1.5rem;
  background: var(--color-accent);
  color: white;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  font-family: inherit;
}

.avatar-upload-btn:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.avatar-upload-btn:active {
  transform: translateY(0) translateX(0);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.avatar-uploader {
  margin-top: 1rem;
}
</style>
