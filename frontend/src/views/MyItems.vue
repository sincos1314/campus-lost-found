<template>
  <div class="my-items-container">
    <el-card class="privacy-card" shadow="never">
      <el-row :gutter="15" align="middle">
        <el-col :span="12">
          <div>
            <span>发布历史可见性：</span>
            <el-radio-group v-model="privacy.visibility_setting" @change="savePrivacy">
              <el-radio label="hidden">隐藏</el-radio>
              <el-radio label="partial">部分隐藏</el-radio>
              <el-radio label="public">不隐藏</el-radio>
            </el-radio-group>
          </div>
        </el-col>
        <el-col :span="12" v-if="privacy.visibility_setting==='partial'">
          <div class="privacy-others">
            <span>其他人默认：</span>
            <el-select v-model="privacy.others_policy" style="width:160px" @change="savePrivacy">
              <el-option label="显示" value="show" />
              <el-option label="隐藏" value="hide" />
            </el-select>
            <el-button style="margin-left:10px" @click="openPrivacyDrawer">配置名单</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>
    <el-card class="stats-card" shadow="never">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="发布总数" :value="stats.my_items">
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="失物发布" :value="stats.my_lost">
            <template #prefix>
              <el-icon><Warning /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="拾物发布" :value="stats.my_found">
            <template #prefix>
              <el-icon><Present /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="已解决" :value="stats.my_solved">
            <template #prefix>
              <el-icon><Check /></el-icon>
            </template>
          </el-statistic>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="filter-card" shadow="never">
      <el-row :gutter="15">
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="全部类型" @change="loadMyItems">
            <el-option label="全部" value="" />
            <el-option label="失物" value="lost" />
            <el-option label="拾物" value="found" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="状态" @change="loadMyItems">
            <el-option label="全部状态" value="" />
            <el-option label="进行中" value="open" />
            <el-option label="已解决" value="closed" />
          </el-select>
        </el-col>
        <el-col :span="12">
          <el-button type="primary" @click="loadMyItems">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-empty v-if="items.length === 0" description="还没有发布任何信息" />

    <el-table v-else :data="items" style="width: 100%" stripe>
      <el-table-column prop="title" label="标题" min-width="200" />
      
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.category === 'lost' ? 'danger' : 'success'" size="small">
            {{ row.category === 'lost' ? '失物' : '拾物' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="item_type" label="物品类型" width="120" />
      
      <el-table-column prop="location" label="地点" min-width="150" />
      
      <el-table-column prop="date" label="日期" width="120" />
      
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'open' ? 'success' : 'info'" size="small">
            {{ row.status === 'open' ? '进行中' : '已解决' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="发布时间" width="180" />

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="viewDetail(row.id)" link>
            查看
          </el-button>
          <el-button type="primary" size="small" @click="openEdit(row)" link>
            修改
          </el-button>
          <el-button
            v-if="row.status === 'open'"
            type="success"
            size="small"
            @click="markSolved(row)"
            link
          >
            标记已解决
          </el-button>
          <el-button type="danger" size="small" @click="deleteItem(row)" link>
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

      <el-dialog v-model="editDialog" title="修改发布信息" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="详细描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="5"
            placeholder="详细描述物品特征、品牌、颜色等信息，便于识别"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="类型" prop="category">
          <el-select v-model="editForm.category">
            <el-option label="失物" value="lost" />
            <el-option label="拾物" value="found" />
          </el-select>
        </el-form-item>
        <el-form-item label="地点" prop="location">
          <el-input v-model="editForm.location" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_name">
          <el-input v-model="editForm.contact_name" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="editForm.contact_phone" />
        </el-form-item>
        <el-form-item label="日期" prop="date">
          <el-date-picker v-model="editForm.date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="物品类型" prop="item_type">
          <el-input v-model="editForm.item_type" />
        </el-form-item>
        <el-form-item label="图片">
          <div class="image-upload-container">
            <div class="image-list" v-if="editImageList.length > 0">
              <div
                v-for="(img, index) in editImageList"
                :key="img.id || index"
                class="image-item"
                :draggable="true"
                @dragstart="handleEditDragStart(index, $event)"
                @dragover.prevent
                @drop="handleEditDrop(index, $event)"
                @dragenter.prevent
              >
                <img :src="img.preview || img.url" class="thumbnail-image" />
                <div class="image-overlay">
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    :icon="Delete"
                    @click="removeEditImage(index)"
                    class="delete-btn"
                  />
                </div>
                <div class="image-index">{{ index + 1 }}</div>
              </div>
            </div>
            <el-upload
              v-if="editImageList.length < 8"
              class="image-uploader"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleEditImageChange"
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
      </el-form>
      <template #footer>
        <el-button @click="editDialog=false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
      </el-dialog>

    <el-drawer v-model="drawerVisible" title="可见名单配置" size="40%">
      <el-row :gutter="20">
        <el-col :span="12">
          <h4>允许查看（show）</h4>
          <div class="bulk">
            <el-button size="small" @click="selectAllShow">全选</el-button>
            <el-button size="small" @click="clearShow">清空</el-button>
          </div>
          <el-checkbox-group v-model="showList" @change="onShowChange">
            <el-checkbox v-for="c in conversations" :key="c.other_user.id" :label="c.other_user.id">
              {{ c.other_user.username }}
            </el-checkbox>
          </el-checkbox-group>
        </el-col>
        <el-col :span="12">
          <h4>禁止查看（hide）</h4>
          <div class="bulk">
            <el-button size="small" @click="selectAllHide">全选</el-button>
            <el-button size="small" @click="clearHide">清空</el-button>
          </div>
          <el-checkbox-group v-model="hideList" @change="onHideChange">
            <el-checkbox v-for="c in conversations" :key="c.other_user.id" :label="c.other_user.id">
              {{ c.other_user.username }}
            </el-checkbox>
          </el-checkbox-group>
        </el-col>
      </el-row>
      <template #footer>
        <el-button @click="drawerVisible=false">取消</el-button>
        <el-button type="primary" @click="savePrivacyRules">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import imageCompression from 'browser-image-compression'
import request from '../utils/request'
import { getUser, getToken } from '../utils/auth'
import { apiOrigin, absoluteUrl, previewList, previewListMultiple } from '../utils/request'

const router = useRouter()
const currentUser = getUser()

const items = ref([])
const stats = ref({
  my_items: 0,
  my_lost: 0,
  my_found: 0,
  my_solved: 0
})

const filters = reactive({
  category: '',
  status: ''
})
const privacy = reactive({ visibility_setting: 'public', others_policy: 'show' })
const drawerVisible = ref(false)
const showList = ref([])
const hideList = ref([])
const conversations = ref([])
const editDialog = ref(false)
const editFormRef = ref()
const editForm = ref({ id: 0, title: '', description: '', category: 'lost', location: '', contact_name: '', contact_phone: '', date: '', item_type: '', image_url: '', image_urls: [] })
const editImageList = ref([]) // 编辑时的图片列表
const editDraggedIndex = ref(null) // 拖拽时的索引
const token = getToken()
const editRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  contact_phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }]
}

const loadMyItems = async () => {
  try {
    const params = {
      ...filters,
      page: 1,
      page_size: 1000
    }
    const res = await request.get('/items', { params })
    const list = Array.isArray(res) ? res : (res.items || [])
    items.value = list.filter(item => item.user_id === currentUser.id)
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const loadPrivacy = async () => {
  try {
    const p = await request.get('/privacy')
    privacy.visibility_setting = p.visibility_setting
    privacy.others_policy = p.others_policy
    showList.value = p.rules.filter(r=>r.rule==='show').map(r=>r.target_user_id)
    hideList.value = p.rules.filter(r=>r.rule==='hide').map(r=>r.target_user_id)
  } catch (e) { console.error(e) }
}

const openPrivacyDrawer = async () => {
  const convs = await request.get('/conversations')
  const seen = new Set()
  conversations.value = convs.filter(c => {
    const id = c?.other_user?.id
    if (!id) return false
    if (seen.has(id)) return false
    seen.add(id)
    return true
  })
  drawerVisible.value = true
}

const savePrivacy = async () => {
  try {
    await request.put('/privacy', { visibility_setting: privacy.visibility_setting, others_policy: privacy.others_policy })
    ElMessage.success('隐私设置已保存')
  } catch (e) { console.error(e) }
}

const savePrivacyRules = async () => {
  try {
    await request.put('/privacy/rules', { show_list: showList.value, hide_list: hideList.value })
    ElMessage.success('名单已更新')
    drawerVisible.value = false
  } catch (e) { console.error(e) }
}

const selectAllShow = () => {
  const ids = conversations.value.map(c => c.other_user.id)
  showList.value = ids
  hideList.value = hideList.value.filter(id => !ids.includes(id))
}
const clearShow = () => { showList.value = [] }
const selectAllHide = () => {
  const ids = conversations.value.map(c => c.other_user.id)
  hideList.value = ids
  showList.value = showList.value.filter(id => !ids.includes(id))
}
const clearHide = () => { hideList.value = [] }
const onShowChange = (arr) => { hideList.value = hideList.value.filter(id => !arr.includes(id)) }
const onHideChange = (arr) => { showList.value = showList.value.filter(id => !arr.includes(id)) }

const loadStats = async () => {
  try {
    stats.value = await request.get('/my-stats')
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const viewDetail = (id) => {
  router.push(`/item/${id}`)
}

const markSolved = async (item) => {
  try {
    await ElMessageBox.confirm('确定要标记为已解决吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await request.put(`/items/${item.id}`, { status: 'closed' })
    ElMessage.success('已标记为已解决')
    loadMyItems()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
    }
  }
}

const deleteItem = async (item) => {
  try {
    await ElMessageBox.confirm('确定要删除这条信息吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    })

    await request.delete(`/items/${item.id}`)
    ElMessage.success('删除成功')
    loadMyItems()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const openEdit = async (item) => {
  // 加载完整的物品信息
  try {
    const fullItem = await request.get(`/items/${item.id}`)
    
    // 初始化表单数据
    editForm.value = {
      id: fullItem.id,
      title: fullItem.title,
      description: fullItem.description,
      category: fullItem.category,
      location: fullItem.location,
      contact_name: fullItem.contact_name,
      contact_phone: fullItem.contact_phone,
      date: fullItem.date,
      item_type: fullItem.item_type,
      image_url: fullItem.image_url || '',
      image_urls: fullItem.image_urls || []
    }
    
    // 初始化图片列表（按顺序显示所有图片）
    editImageList.value = []
    if (fullItem.image_urls && Array.isArray(fullItem.image_urls) && fullItem.image_urls.length > 0) {
      // 使用 image_urls（多图）
      editImageList.value = fullItem.image_urls.map((url, index) => {
        // 从 URL 中提取文件名
        let filename = url
        if (url.startsWith('/api/image/')) {
          filename = url.replace('/api/image/', '')
          // URL 解码，处理可能的编码字符
          try {
            filename = decodeURIComponent(filename)
          } catch (e) {
            // 如果解码失败，使用原始文件名
            console.warn('文件名解码失败:', filename, e)
          }
        }
        return {
          id: `existing_${index}_${filename}`, // 使用文件名确保唯一性
          url: url,
          preview: absoluteUrl(url),
          isExisting: true, // 标记为已存在的图片
          originalUrl: url,
          filename: filename // 保存文件名用于提交
        }
      })
    } else if (fullItem.image_url) {
      // 向后兼容：只有单图
      let filename = fullItem.image_url
      if (filename.startsWith('/api/image/')) {
        filename = filename.replace('/api/image/', '')
        // URL 解码，处理可能的编码字符
        try {
          filename = decodeURIComponent(filename)
        } catch (e) {
          // 如果解码失败，使用原始文件名
          console.warn('文件名解码失败:', filename, e)
        }
      }
      editImageList.value = [{
        id: `existing_0_${filename}`,
        url: fullItem.image_url,
        preview: absoluteUrl(fullItem.image_url),
        isExisting: true,
        originalUrl: fullItem.image_url,
        filename: filename
      }]
    }
    
    editDialog.value = true
  } catch (error) {
    console.error('加载物品详情失败:', error)
    ElMessage.error('加载失败')
  }
}

const submitEdit = async () => {
  try {
    await editFormRef.value.validate()
    
    // 分离新图片和已存在的图片
    const newImages = editImageList.value.filter(img => !img.isExisting)
    const existingImages = editImageList.value.filter(img => img.isExisting)
    
    // 只要有图片（无论是否有变化），都需要更新图片顺序
    // 这样可以确保拖拽排序后的顺序被保存
    if (editImageList.value.length > 0) {
      const formData = new FormData()
      
      // 添加要保留的已存在图片（按当前顺序）
      existingImages.forEach(img => {
        // 优先使用 filename，如果没有则从 URL 提取
        let imagePath = img.filename
        if (!imagePath) {
          imagePath = img.originalUrl || img.url
          if (imagePath.startsWith('/api/image/')) {
            imagePath = imagePath.replace('/api/image/', '')
            // URL 解码，处理可能的编码字符
            try {
              imagePath = decodeURIComponent(imagePath)
            } catch (e) {
              // 如果解码失败，使用原始路径
              console.warn('文件名解码失败:', imagePath, e)
            }
          }
        }
        if (imagePath) {
          formData.append('keep_existing', imagePath)
        }
      })
      
      // 添加新上传的图片（按顺序）
      newImages.forEach((img, index) => {
        const position = existingImages.length + index
        if (position === 0) {
          formData.append('image', img.file) // 主图
        } else {
          formData.append('images', img.file) // 副图
        }
      })
      
      // 更新图片（即使只是顺序改变也会更新）
      await request.post(`/items/${editForm.value.id}/images`, formData)
    } else {
      // 如果所有图片都被删除了，需要清空图片
      await request.delete(`/items/${editForm.value.id}/image`)
    }
    
    // 更新其他信息
    const payload = {
      title: editForm.value.title,
      description: editForm.value.description,
      category: editForm.value.category,
      location: editForm.value.location,
      contact_name: editForm.value.contact_name,
      contact_phone: editForm.value.contact_phone,
      date: editForm.value.date,
      item_type: editForm.value.item_type
    }
    await request.put(`/items/${editForm.value.id}`, payload)
    
    ElMessage.success('修改成功')
    editDialog.value = false
    await loadMyItems()
  } catch (e) {
    console.error('修改失败:', e)
    ElMessage.error('修改失败')
  }
}

// 编辑时的图片处理函数
const handleEditImageChange = async (file, fileList) => {
  // 检查是否已达到8张限制
  if (editImageList.value.length >= 8) {
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
      useWebWorker: true,
      fileType: file.raw.type,
      initialQuality: 0.8
    }

    const loadingMessage = ElMessage({
      message: '正在压缩图片...',
      type: 'info',
      duration: 0
    })

    const compressedBlob = await imageCompression(file.raw, options)
    
    const originalName = file.raw.name || `image_${Date.now()}.jpg`
    const fileExtension = originalName.split('.').pop() || 'jpg'
    const fileName = originalName.replace(/\.[^/.]+$/, '') || 'image'
    const compressedFile = new File(
      [compressedBlob], 
      `${fileName}_compressed.${fileExtension}`, 
      { type: compressedBlob.type || file.raw.type }
    )
    
    loadingMessage.close()

    const compressedSizeMB = compressedFile.size / 1024 / 1024
    const compressionRatio = ((1 - compressedFile.size / file.raw.size) * 100).toFixed(1)
    
    if (compressionRatio > 20) {
      ElMessage.success(`图片已压缩：${originalSizeMB.toFixed(2)}MB → ${compressedSizeMB.toFixed(2)}MB (减少 ${compressionRatio}%)`)
    }

    // 检查总大小
    const currentTotalSize = editImageList.value
      .filter(img => !img.isExisting && img.file)
      .reduce((sum, img) => sum + img.file.size, 0)
    const newTotalSize = currentTotalSize + compressedFile.size
    const maxTotalSize = 20 * 1024 * 1024 // 20MB

    if (newTotalSize > maxTotalSize) {
      const currentTotalMB = (currentTotalSize / 1024 / 1024).toFixed(2)
      ElMessage.error(`图片总大小不能超过20MB（压缩后）！当前已上传 ${currentTotalMB}MB，此图片 ${compressedSizeMB.toFixed(2)}MB`)
      return false
    }

    // 创建预览
    const reader = new FileReader()
    reader.onload = (e) => {
      if (editImageList.value.length >= 8) {
        ElMessage.warning('最多只能上传8张图片')
        return
      }
      editImageList.value.push({
        id: `new_${Date.now()}_${Math.random()}`,
        file: compressedFile,
        preview: e.target.result,
        isExisting: false
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

const removeEditImage = (index) => {
  editImageList.value.splice(index, 1)
}

const handleEditDragStart = (index, event) => {
  editDraggedIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
}

const handleEditDrop = (index, event) => {
  event.preventDefault()
  if (editDraggedIndex.value === null || editDraggedIndex.value === index) return
  
  const draggedItem = editImageList.value[editDraggedIndex.value]
  editImageList.value.splice(editDraggedIndex.value, 1)
  editImageList.value.splice(index, 0, draggedItem)
  editDraggedIndex.value = null
}

onMounted(() => {
  loadMyItems()
  loadStats()
  loadPrivacy()
})
</script>

<style scoped>
.my-items-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.stats-card,
.filter-card,
.privacy-card {
  margin-bottom: 2rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 1.5rem;
}

.privacy-others { display:flex; align-items:center; gap:8px; }
.bulk { display:flex; gap:8px; margin:8px 0; }

.my-items-container :deep(.el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 700;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.my-items-container :deep(.el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

.my-items-container :deep(.el-button--primary:hover) {
  background: var(--color-accent) !important;
  color: white !important;
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.my-items-container :deep(.el-button--success) {
  background: #48bb78;
  color: white !important;
}

.my-items-container :deep(.el-button--success:hover) {
  background: #48bb78 !important;
  color: white !important;
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.my-items-container :deep(.el-button--danger) {
  background: #f56565;
  color: white !important;
}

.my-items-container :deep(.el-button--danger:hover) {
  background: #f56565 !important;
  color: white !important;
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.my-items-container :deep(.el-button.is-link) {
  background: transparent;
  border: none;
  box-shadow: none;
  color: var(--color-accent) !important;
  font-weight: 700;
}

.my-items-container :deep(.el-button.is-link:hover) {
  background: transparent !important;
  color: var(--color-accent) !important;
  transform: none;
  box-shadow: none;
}

/* 移除 Element Plus 默认的输入框包装器样式 */
.my-items-container :deep(.el-input),
.my-items-container :deep(.el-select),
.my-items-container :deep(.el-date-editor) {
  border: none !important;
  box-shadow: none !important;
}

.my-items-container :deep(.el-input__wrapper),
.my-items-container :deep(.el-select__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

.my-items-container :deep(.el-input__inner),
.my-items-container :deep(.el-select__placeholder),
.my-items-container :deep(.el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.my-items-container :deep(.el-input__wrapper.is-focus),
.my-items-container :deep(.el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.my-items-container :deep(.el-table) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
}

/* 编辑对话框中的图片上传样式 */
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

/* 编辑对话框中的详细描述样式（与 PostItem 一致） */
.my-items-container :deep(.el-textarea) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

.my-items-container :deep(.el-table th) {
  background: var(--color-primary);
  color: var(--color-text);
  font-weight: 900;
  font-size: 0.95rem;
}

.my-items-container :deep(.el-table td) {
  font-weight: 600;
  color: var(--color-text);
}

/* 对话框中的输入框样式 */
.my-items-container :deep(.el-dialog) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.my-items-container :deep(.el-dialog .el-input),
.my-items-container :deep(.el-dialog .el-select),
.my-items-container :deep(.el-dialog .el-date-editor),
.my-items-container :deep(.el-dialog .el-textarea) {
  border: none !important;
  box-shadow: none !important;
}

.my-items-container :deep(.el-dialog .el-input__wrapper),
.my-items-container :deep(.el-dialog .el-select__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

/* textarea 特殊处理 - el-input type="textarea" 会渲染为 el-textarea */
.my-items-container :deep(.el-dialog .el-textarea) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

/* textarea 的 inner 使用与其他输入框相同的边框样式 */
.my-items-container :deep(.el-dialog .el-textarea__inner) {
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

/* 确保字符计数在框内显示 */
.my-items-container :deep(.el-dialog .el-input__count) {
  background: transparent !important;
  color: #909399 !important;
}

.my-items-container :deep(.el-dialog .el-input__inner),
.my-items-container :deep(.el-dialog .el-select__placeholder),
.my-items-container :deep(.el-dialog .el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

/* textarea 的 inner 不应该在这里设置 border: none，因为我们需要边框 */
.my-items-container :deep(.el-dialog .el-textarea__inner) {
  /* 不设置 border: none，保持之前设置的边框样式 */
  background: var(--color-card) !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.my-items-container :deep(.el-dialog .el-input__wrapper.is-focus),
.my-items-container :deep(.el-dialog .el-textarea__inner:focus),
.my-items-container :deep(.el-dialog .el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

/* 确保 textarea 的 focus 状态也有阴影效果 */
.my-items-container :deep(.el-dialog .el-textarea__inner:focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.my-items-container :deep(.el-dialog .el-date-editor .el-input__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
}

.my-items-container :deep(.el-dialog .el-date-editor .el-input__wrapper.is-focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
}
</style>
