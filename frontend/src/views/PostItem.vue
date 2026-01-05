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
          <div class="image-upload-container">
            <div class="image-list" v-if="imageList.length > 0">
              <div
                v-for="(img, index) in imageList"
                :key="index"
                class="image-item"
                :draggable="true"
                @dragstart="handleDragStart(index, $event)"
                @dragover.prevent
                @drop="handleDrop(index, $event)"
                @dragenter.prevent
              >
                <img :src="img.preview" class="thumbnail-image" />
                <div class="image-overlay">
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    :icon="Delete"
                    @click="removeImage(index)"
                    class="delete-btn"
                  />
                </div>
                <div class="image-index">{{ index + 1 }}</div>
              </div>
            </div>
            <el-upload
              v-if="imageList.length < 8"
              class="image-uploader"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleImageChange"
              :multiple="true"
              accept="image/*"
            >
              <el-icon class="uploader-icon"><Plus /></el-icon>
            </el-upload>
          </div>
          <div class="upload-tip">
            <el-text type="info" size="small">
              支持 jpg、png、gif 格式，每张原始大小不超过10MB，上传前会自动压缩，最多上传8张，第一张将作为主图
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
import { Plus, Delete } from '@element-plus/icons-vue'
import imageCompression from 'browser-image-compression'
import request from '../utils/request'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const imageList = ref([])
const draggedIndex = ref(null)

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

const handleImageChange = async (file, fileList) => {
  // 检查是否已达到8张限制
  if (imageList.value.length >= 8) {
    ElMessage.warning('最多只能上传8张图片，请先删除部分图片后再上传')
    return false
  }

  const isImage = file.raw.type.startsWith('image/')
  const originalSizeMB = file.raw.size / 1024 / 1024

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  
  // 检查原始文件大小（最大 10MB）
  if (originalSizeMB > 10) {
    ElMessage.error('图片大小不能超过10MB！')
    return false
  }

  try {
    // 压缩图片
    const options = {
      maxSizeMB: 2, // 压缩后最大 2MB
      maxWidthOrHeight: 1920, // 最大宽度或高度
      useWebWorker: true, // 使用 Web Worker 提高性能
      fileType: file.raw.type, // 保持原始格式
      initialQuality: 0.8 // 初始质量 80%
    }

    // 显示压缩提示
    const loadingMessage = ElMessage({
      message: '正在压缩图片...',
      type: 'info',
      duration: 0 // 不自动关闭
    })

    const compressedBlob = await imageCompression(file.raw, options)
    
    // 将 Blob 转换为 File 对象，保留原始文件名
    // 如果原始文件名不存在，生成一个带时间戳的文件名
    const originalName = file.raw.name || `image_${Date.now()}.jpg`
    const fileExtension = originalName.split('.').pop() || 'jpg'
    const fileName = originalName.replace(/\.[^/.]+$/, '') || 'image'
    const compressedFile = new File(
      [compressedBlob], 
      `${fileName}_compressed.${fileExtension}`, 
      { type: compressedBlob.type || file.raw.type }
    )
    
    // 关闭加载提示
    loadingMessage.close()

    const compressedSizeMB = compressedFile.size / 1024 / 1024
    const compressionRatio = ((1 - compressedFile.size / file.raw.size) * 100).toFixed(1)
    
    // 如果压缩效果明显，显示提示
    if (compressionRatio > 20) {
      ElMessage.success(`图片已压缩：${originalSizeMB.toFixed(2)}MB → ${compressedSizeMB.toFixed(2)}MB (减少 ${compressionRatio}%)`)
    }

    // 检查总大小（8张 × 2MB = 16MB，留有余地设为 20MB）
    const currentTotalSize = imageList.value.reduce((sum, img) => sum + img.file.size, 0)
    const newTotalSize = currentTotalSize + compressedFile.size
    const maxTotalSize = 20 * 1024 * 1024 // 20MB（压缩后）

    if (newTotalSize > maxTotalSize) {
      const currentTotalMB = (currentTotalSize / 1024 / 1024).toFixed(2)
      ElMessage.error(`图片总大小不能超过20MB（压缩后）！当前已上传 ${currentTotalMB}MB，此图片 ${compressedSizeMB.toFixed(2)}MB`)
      return false
    }

    // 创建预览
    const reader = new FileReader()
    reader.onload = (e) => {
      // 再次检查，防止在异步处理过程中超过限制
      if (imageList.value.length >= 8) {
        ElMessage.warning('最多只能上传8张图片')
        return
      }
      imageList.value.push({
        file: compressedFile, // 使用压缩后的文件（现在是 File 对象，有正确的文件名）
        preview: e.target.result,
        originalFile: file.raw // 保存原文件引用（如果需要）
      })
    }
    reader.readAsDataURL(compressedFile)
    
    return true
  } catch (error) {
    console.error('图片压缩失败:', error)
    ElMessage.error('图片压缩失败，请重试')
    return false
  }
}

const removeImage = (index) => {
  imageList.value.splice(index, 1)
}

const handleDragStart = (index, event) => {
  draggedIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
}

const handleDrop = (index, event) => {
  event.preventDefault()
  if (draggedIndex.value === null || draggedIndex.value === index) return
  
  const draggedItem = imageList.value[draggedIndex.value]
  imageList.value.splice(draggedIndex.value, 1)
  imageList.value.splice(index, 0, draggedItem)
  draggedIndex.value = null
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
      
      // 按顺序上传图片，第一张作为主图
      imageList.value.forEach((img, index) => {
        if (index === 0) {
          formData.append('image', img.file) // 主图
        } else {
          formData.append('images', img.file) // 副图
        }
      })

      // 调试：检查 FormData 内容
      console.log('[DEBUG] 准备上传的图片数量:', imageList.value.length)
      for (let pair of formData.entries()) {
        console.log('[DEBUG] FormData:', pair[0], pair[1])
      }

      const response = await request.post('/items', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      console.log('[DEBUG] 服务器返回的数据:', response)
      console.log('[DEBUG] image_url:', response.image_url)
      console.log('[DEBUG] image_urls:', response.image_urls)

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
  imageList.value = []
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
  margin: 2rem auto;
  padding: 0 2rem;
}

.post-card {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 2rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-header h2 {
  margin: 0;
  color: var(--color-text);
  font-size: 1.8rem;
  font-weight: 900;
}

.image-upload-container {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.image-item {
  position: relative;
  width: 120px;
  height: 120px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  overflow: hidden;
  cursor: move;
  transition: all 0.15s ease;
  background: var(--color-card);
}

.image-item:hover {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.image-item.dragging {
  opacity: 0.5;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.delete-btn {
  background: rgba(245, 101, 101, 0.9);
  border: none;
}

.image-index {
  position: absolute;
  top: 4px;
  left: 4px;
  background: var(--color-accent);
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  border: 2px solid var(--color-card);
}

.image-uploader {
  width: 120px;
  height: 120px;
  border: var(--border-width) dashed var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  overflow: hidden;
  transition: all 0.15s ease;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-uploader:hover {
  border-color: var(--border-color);
  border-style: solid;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.uploader-icon {
  font-size: 40px;
  color: #8c939d;
}

.upload-tip {
  margin-top: 10px;
}

.post-card :deep(.el-form-item__label) {
  font-weight: 700;
  color: var(--color-text);
}

/* 移除 Element Plus 默认的输入框包装器样式 - 仿照 textarea 的方式 */
.post-card :deep(.el-input),
.post-card :deep(.el-select),
.post-card :deep(.el-date-editor),
.post-card :deep(.el-textarea) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

/* 输入框和选择框的包装器是唯一有边框的外层（仿照 textarea__inner） */
.post-card :deep(.el-input__wrapper),
.post-card :deep(.el-input__wrapper.is-focus),
.post-card :deep(.el-input__wrapper:hover),
.post-card :deep(.el-select__wrapper),
.post-card :deep(.el-select__wrapper.is-focused),
.post-card :deep(.el-select__wrapper:hover) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

/* textarea 特殊处理 - el-textarea 本身不应该有边框（这是正确的） */
.post-card :deep(.el-textarea) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

/* textarea 的 inner 是唯一的边框容器（这是正确的，保持不变） */
.post-card :deep(.el-textarea__inner) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  color: var(--color-text) !important;
  min-height: auto !important;
}

/* 内部元素完全透明，没有任何边框、背景、阴影（仿照 textarea 内部） */
.post-card :deep(.el-input__inner),
.post-card :deep(.el-input__inner:focus),
.post-card :deep(.el-input__inner:hover),
.post-card :deep(.el-select__placeholder),
.post-card :deep(.el-select__selected-item),
.post-card :deep(.el-select__caret),
.post-card :deep(.el-select__suffix),
.post-card :deep(.el-select__prefix),
.post-card :deep(.el-input__prefix),
.post-card :deep(.el-input__suffix),
.post-card :deep(.el-input__prefix-inner),
.post-card :deep(.el-input__suffix-inner) {
  border: none !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

/* 焦点状态的硬阴影（只在外层） */
.post-card :deep(.el-input__wrapper.is-focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.post-card :deep(.el-textarea__inner:focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.post-card :deep(.el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

/* 日期选择器 */
.post-card :deep(.el-date-editor.el-input) {
  width: 100% !important;
}

.post-card :deep(.el-date-editor .el-input__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
}

.post-card :deep(.el-date-editor .el-input__wrapper.is-focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
}

/* 移除输入框前缀图标的默认样式 */
.post-card :deep(.el-input__prefix) {
  color: var(--color-text) !important;
}

/* 单选按钮组 */
.post-card :deep(.el-radio-group) {
  display: flex;
  gap: 1rem;
}

.post-card :deep(.el-radio) {
  font-weight: 700;
  color: var(--color-text);
}

.post-card :deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
}

.post-card :deep(.el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.post-card :deep(.el-button--primary) {
  background: var(--color-accent);
  color: white;
}

.post-card :deep(.el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.post-card :deep(.el-button:active) {
  transform: translateY(0) translateX(0);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}
</style>
