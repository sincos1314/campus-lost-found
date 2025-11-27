<template>
  <div class="post-container">
    <el-card class="post-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h2>发布信息</h2>
          <el-tag :type="form.category === 'lost' ? 'danger' : 'success'">
            {{ form.category === 'lost' ? '失物' : '拾物' }}
          </el-tag>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        size="large"
      >
        <el-form-item label="信息类型" prop="category">
          <el-radio-group v-model="form.category">
            <el-radio label="lost">失物（我丢了东西）</el-radio>
            <el-radio label="found">拾物（我捡到东西）</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="物品类型" prop="item_type">
          <el-select v-model="form.item_type" placeholder="请选择物品类型">
            <el-option label="手机" value="手机" />
            <el-option label="钱包" value="钱包" />
            <el-option label="钥匙" value="钥匙" />
            <el-option label="身份证/学生证" value="身份证/学生证" />
            <el-option label="书籍" value="书籍" />
            <el-option label="衣物" value="衣物" />
            <el-option label="电子产品" value="电子产品" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="简短描述物品，如：黑色iPhone 14手机"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="详细描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            placeholder="详细描述物品特征、品牌、颜色等信息，便于识别"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="地点" prop="location">
          <el-input
            v-model="form.location"
            placeholder="丢失/拾取地点，如：图书馆三楼"
          >
            <template #prefix>
              <el-icon><Location /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="日期" prop="date">
          <el-date-picker
            v-model="form.date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="联系人" prop="contact_name">
          <el-input
            v-model="form.contact_name"
            placeholder="您的姓名"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="联系电话" prop="contact_phone">
          <el-input
            v-model="form.contact_phone"
            placeholder="您的手机号"
          >
            <template #prefix>
              <el-icon><Phone /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="上传图片">
          <el-upload
            class="image-uploader"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageChange"
            accept="image/*"
          >
            <img v-if="imagePreview" :src="imagePreview" class="preview-image" />
            <el-icon v-else class="uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">
            <el-text type="info" size="small">
              支持 jpg、png、gif 格式，大小不超过5MB
            </el-text>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            提交发布
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const imageFile = ref(null)
const imagePreview = ref('')

const form = reactive({
  category: 'lost',
  item_type: '手机',
  title: '',
  description: '',
  location: '',
  date: new Date().toISOString().split('T')[0],
  contact_name: '',
  contact_phone: ''
})

const rules = {
  category: [{ required: true, message: '请选择信息类型', trigger: 'change' }],
  item_type: [{ required: true, message: '请选择物品类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入详细描述', trigger: 'blur' }],
  location: [{ required: true, message: '请输入地点', trigger: 'blur' }],
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  contact_name: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
  contact_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const handleImageChange = (file) => {
  const isImage = file.raw.type.startsWith('image/')
  const isLt5M = file.raw.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过5MB！')
    return
  }

  imageFile.value = file.raw
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const formData = new FormData()
      Object.keys(form).forEach(key => {
        formData.append(key, form[key])
      })
      if (imageFile.value) {
        formData.append('image', imageFile.value)
      }

      await request.post('/items', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      ElMessage.success('发布成功！')
      router.push(`/list/${form.category}`)
    } catch (error) {
      console.error('发布失败:', error)
    } finally {
      loading.value = false
    }
  })
}

const handleReset = () => {
  formRef.value?.resetFields()
  imageFile.value = null
  imagePreview.value = ''
}

onMounted(() => {
  // 如果从首页传来category参数，设置默认值
  if (route.query.category) {
    form.category = route.query.category
  }
})
</script>

<style scoped>
.post-container {
  max-width: 800px;
  margin: 0 auto;
}

.post-card {
  border-radius: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
}

.image-uploader {
  width: 180px;
  height: 180px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.3s;
}

.image-uploader:hover {
  border-color: #667eea;
}

.uploader-icon {
  font-size: 40px;
  color: #8c939d;
  width: 180px;
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-tip {
  margin-top: 10px;
}
</style>
