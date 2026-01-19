<template>
  <div class="claim-management-container">
    <el-card class="header-card" shadow="never">
      <h2>
        <el-icon><Trophy /></el-icon>
        认领管理
      </h2>
      <p class="subtitle">统一处理所有待处理的认领申请</p>
    </el-card>

    <el-card class="filter-card" shadow="never" v-if="claims.length > 0">
      <el-row :gutter="15">
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="全部状态" @change="loadClaims">
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="已批准" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="物品类型" @change="loadClaims">
            <el-option label="全部" value="" />
            <el-option label="失物" value="lost" />
            <el-option label="拾物" value="found" />
          </el-select>
        </el-col>
        <el-col :span="12">
          <el-button type="primary" @click="loadClaims">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-empty v-if="!loading && claims.length === 0" description="暂无待处理的认领申请" :image-size="150" />

    <div v-else class="claims-list">
      <el-card
        v-for="claim in filteredClaims"
        :key="claim.id"
        class="claim-card"
        shadow="hover"
      >
        <div class="claim-header">
          <div class="claim-item-info">
            <h3 @click="goToItem(claim.item_id)" class="item-title-link">
              {{ claim.item?.title || '物品已删除' }}
            </h3>
            <div class="item-tags">
              <el-tag
                :type="claim.item?.category === 'lost' ? 'danger' : 'success'"
                size="small"
              >
                {{ claim.item?.category === 'lost' ? '失物' : '拾物' }}
              </el-tag>
              <el-tag
                :type="claim.item?.status === 'open' ? 'success' : 'info'"
                size="small"
              >
                {{ claim.item?.status === 'open' ? '进行中' : '已解决' }}
              </el-tag>
            </div>
          </div>
          <div class="claim-status">
            <el-tag
              :type="claim.status === 'approved' ? 'success' : claim.status === 'rejected' ? 'danger' : 'warning'"
              size="small"
            >
              {{ claim.status === 'approved' ? '已批准' : claim.status === 'rejected' ? '已拒绝' : '待处理' }}
            </el-tag>
          </div>
        </div>

        <div class="claim-content">
          <div class="claimant-info">
            <el-icon><User /></el-icon>
            <span class="claimant-name">{{ claim.claimant_username }}</span>
            <span class="claim-time">
              <el-icon><Clock /></el-icon>
              {{ formatTime(claim.created_at) }}
            </span>
          </div>

          <div class="claim-description" v-if="claim.description">
            <strong>认领说明：</strong>
            <p>{{ claim.description }}</p>
          </div>

          <!-- 认领证据图片 -->
          <div v-if="claim.image_urls && claim.image_urls.length > 0" class="claim-images">
            <div class="claim-images-title">证据图片：</div>
            <div class="claim-images-grid">
              <el-image
                v-for="(imageUrl, index) in claim.image_urls"
                :key="index"
                :src="absoluteUrl(imageUrl)"
                :preview-src-list="claim.image_urls.map(url => absoluteUrl(url))"
                :initial-index="index"
                fit="cover"
                class="claim-image-item"
                :preview-teleported="true"
              />
            </div>
          </div>

          <div class="item-info-summary">
            <div class="info-item">
              <el-icon><Location /></el-icon>
              <span>{{ claim.item?.location }}</span>
            </div>
            <div class="info-item">
              <el-icon><Calendar /></el-icon>
              <span>{{ claim.item?.date }}</span>
            </div>
            <div class="info-item">
              <el-icon><Box /></el-icon>
              <span>{{ claim.item?.item_type }}</span>
            </div>
          </div>
        </div>

        <div class="claim-footer" v-if="claim.status === 'pending'">
          <el-button type="success" @click="approveClaim(claim.id)">
            <el-icon><Check /></el-icon>
            批准认领
          </el-button>
          <el-button type="danger" @click="rejectClaim(claim.id)">
            <el-icon><Close /></el-icon>
            拒绝认领
          </el-button>
          <el-button type="primary" @click="contactClaimant(claim.claimant_id)">
            <el-icon><ChatDotRound /></el-icon>
            联系申请认领者
          </el-button>
          <el-button type="primary" @click="goToItem(claim.item_id)">
            查看物品详情
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Trophy, Refresh, User, Clock, Location, Calendar, Box, Check, Close, ChatDotRound } from '@element-plus/icons-vue'
import request from '../utils/request'
import { absoluteUrl } from '../utils/request'
import { isLoggedIn, getUser } from '../utils/auth'

const router = useRouter()
const loading = ref(false)
const claims = ref([])
const filters = ref({
  status: 'pending', // 默认只显示待处理
  category: ''
})

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor(diff / (1000 * 60))

  if (days > 0) {
    return `${days}天前`
  } else if (hours > 0) {
    return `${hours}小时前`
  } else if (minutes > 0) {
    return `${minutes}分钟前`
  } else {
    return '刚刚'
  }
}

// 过滤认领列表
const filteredClaims = computed(() => {
  let result = claims.value

  if (filters.value.status) {
    result = result.filter(claim => claim.status === filters.value.status)
  }

  if (filters.value.category && filters.value.category !== '') {
    result = result.filter(claim => claim.item?.category === filters.value.category)
  }

  return result
})

// 加载认领申请
const loadClaims = async () => {
  if (!isLoggedIn()) {
    return
  }

  loading.value = true
  try {
    // 获取所有状态的认领（用于前端筛选）
    const params = { status: '' }
    claims.value = await request.get('/pending-claims', { params })
  } catch (error) {
    console.error('加载认领申请失败:', error)
    if (error.response?.status === 403) {
      ElMessage.warning('您没有认领申请')
    } else {
      ElMessage.error('加载认领申请失败')
    }
    claims.value = []
  } finally {
    loading.value = false
  }
}

// 批准认领
const approveClaim = async (claimId) => {
  try {
    await ElMessageBox.confirm('确定要批准这个认领申请吗？', '确认批准', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success'
    })
    
    await request.put(`/claims/${claimId}/approve`)
    ElMessage.success('认领申请已批准')
    
    // 重新加载认领列表
    await loadClaims()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批准认领失败:', error)
      ElMessage.error(error.response?.data?.message || '操作失败')
    }
  }
}

// 拒绝认领
const rejectClaim = async (claimId) => {
  try {
    await ElMessageBox.confirm('确定要拒绝这个认领申请吗？', '确认拒绝', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await request.put(`/claims/${claimId}/reject`)
    ElMessage.success('认领申请已拒绝')
    
    // 重新加载认领列表
    await loadClaims()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('拒绝认领失败:', error)
      ElMessage.error(error.response?.data?.message || '操作失败')
    }
  }
}

// 联系申请认领者
const contactClaimant = async (claimantId) => {
  try {
    const currentUser = getUser()
    if (currentUser && claimantId === currentUser.id) {
      ElMessage.warning("不能与自己创建会话");
      return;
    }
    // 获取或创建与认领者的会话
    const conversation = await request.post(
      `/conversations/${claimantId}`
    );
    // 跳转到聊天页面
    router.push(`/chat/${conversation.id}`);
  } catch (error) {
    console.error("创建会话失败:", error);
    ElMessage.error("操作失败");
  }
};

// 跳转到物品详情
const goToItem = (itemId) => {
  router.push(`/item/${itemId}`)
}

onMounted(() => {
  if (isLoggedIn()) {
    loadClaims()
  }
})
</script>

<style scoped>
.claim-management-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.header-card {
  margin-bottom: 1.5rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 1.5rem;
}

.header-card h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  margin: 0;
}

.filter-card {
  margin-bottom: 1.5rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 1rem;
}

.claims-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.claim-card {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.claim-card:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.claim-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: var(--border-width) solid var(--border-color);
}

.claim-item-info {
  flex: 1;
}

.item-title-link {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-accent);
  cursor: pointer;
  transition: color 0.2s ease;
}

.item-title-link:hover {
  color: var(--color-text);
  text-decoration: underline;
}

.item-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.claim-content {
  margin-bottom: 1rem;
}

.claimant-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--color-primary);
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}

.claimant-name {
  font-weight: 700;
  color: var(--color-text);
  margin-right: auto;
}

.claim-time {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.claim-description {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--color-primary);
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}

.claim-description strong {
  color: var(--color-text);
  font-weight: 700;
}

.claim-description p {
  margin: 0.5rem 0 0 0;
  color: var(--color-text);
  line-height: 1.6;
  white-space: pre-wrap;
}

.claim-images {
  margin-bottom: 1rem;
}

.claim-images-title {
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.claim-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.5rem;
}

.claim-image-item {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.claim-image-item:hover {
  transform: scale(1.05);
}

.item-info-summary {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 0.75rem;
  background: var(--color-primary);
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.claim-footer {
  display: flex;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: var(--border-width) solid var(--border-color);
  flex-wrap: wrap;
}

/* 响应式 */
@media (max-width: 768px) {
  .claim-management-container {
    padding: 0 1rem;
  }

  .claim-footer {
    flex-direction: column;
  }

  .claim-footer .el-button {
    width: 100%;
  }
}
</style>
