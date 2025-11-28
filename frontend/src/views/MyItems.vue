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
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" />
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
        <el-form-item label="当前图片">
          <el-image
            v-if="editForm.image_url"
            :src="absoluteUrl(editForm.image_url)"
            :preview-src-list="previewList(editForm.image_url)"
            fit="cover"
            style="max-width:100%; border-radius:8px"
          />
          <div v-else>暂无图片</div>
          <div style="margin-top:8px">
            <el-button v-if="editForm.image_url" type="danger" plain @click="handleImageDelete">删除图片</el-button>
          </div>
        </el-form-item>
        <el-form-item label="图片">
          <el-upload
            :action="`${apiOrigin}/api/items/${editForm.id}/image`"
            :headers="{ Authorization: `Bearer ${token}` }"
            name="image"
            :show-file-list="false"
            :on-success="handleImageSuccess"
            :on-error="handleImageError"
          >
            <el-button type="primary" plain>更换图片</el-button>
          </el-upload>
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
import request from '../utils/request'
import { getUser, getToken } from '../utils/auth'
import { apiOrigin, absoluteUrl, previewList } from '../utils/request'

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
const editForm = ref({ id: 0, title: '', description: '', category: 'lost', location: '', contact_name: '', contact_phone: '', date: '', item_type: '', image_url: '' })
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

const openEdit = (item) => {
  editForm.value = {
    id: item.id,
    title: item.title,
    description: item.description,
    category: item.category,
    location: item.location,
    contact_name: item.contact_name,
    contact_phone: item.contact_phone,
    date: item.date,
    item_type: item.item_type,
    image_url: item.image_url || ''
  }
  editDialog.value = true
}

const submitEdit = async () => {
  try {
    await editFormRef.value.validate()
    const payload = { ...editForm.value }
    delete payload.id
    await request.put(`/items/${editForm.value.id}`, payload)
    ElMessage.success('修改成功')
    editDialog.value = false
    loadMyItems()
  } catch (e) {
    console.error(e)
    ElMessage.error('修改失败')
  }
}

const handleImageSuccess = async () => {
  ElMessage.success('图片已更新')
  try {
    const updated = await request.get(`/items/${editForm.value.id}`)
    editForm.value.image_url = updated.image_url || ''
    await loadMyItems()
  } catch (e) {
    console.error(e)
  }
}
const handleImageDelete = async () => {
  try {
    await request.delete(`/items/${editForm.value.id}/image`)
    editForm.value.image_url = ''
    ElMessage.success('图片已删除')
    await loadMyItems()
  } catch (e) {
    console.error(e)
    ElMessage.error('删除失败')
  }
}
const handleImageError = () => {
  ElMessage.error('图片更新失败')
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
}

.stats-card,
.filter-card {
  margin-bottom: 20px;
  border-radius: 10px;
}

.privacy-card { margin-bottom: 20px; }
.privacy-others { display:flex; align-items:center; gap:8px; }
.bulk { display:flex; gap:8px; margin:8px 0; }
</style>
