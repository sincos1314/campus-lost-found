<template>
  <div class="my-claims-container">
    <el-card class="header-card" shadow="never">
      <h2>
        <el-icon><Trophy /></el-icon>
        我的认领记录
      </h2>
    </el-card>

    <el-card class="filter-card" shadow="never">
      <el-row :gutter="15">
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="全部状态" @change="loadClaims">
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="已批准" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-col>
        <el-col :span="18">
          <el-button type="primary" @click="loadClaims">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-empty v-if="!loading && claims.length === 0" description="还没有认领记录" />

    <div v-else class="claims-list">
      <el-card
        v-for="claim in claims"
        :key="claim.id"
        class="claim-card"
        shadow="hover"
      >
        <div class="claim-header">
          <div class="claim-item-info">
            <h3 @click="goToItem(claim.item_id)" class="item-title-link">
              {{ claim.item?.title || '物品已删除' }}
            </h3>
            <el-tag
              :type="claim.item?.category === 'lost' ? 'danger' : 'success'"
              size="small"
            >
              {{ claim.item?.category === 'lost' ? '失物' : '拾物' }}
            </el-tag>
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

          <div class="claim-meta">
            <span class="claim-time">
              <el-icon><Clock /></el-icon>
              认领时间：{{ formatTime(claim.created_at) }}
            </span>
            <span v-if="claim.updated_at && claim.updated_at !== claim.created_at" class="claim-time">
              <el-icon><Edit /></el-icon>
              更新时间：{{ formatTime(claim.updated_at) }}
            </span>
          </div>
        </div>

        <div class="claim-footer">
          <div class="claim-privacy">
            <el-switch
              v-model="claim.is_public"
              active-text="公开"
              inactive-text="隐藏"
              @change="togglePublic(claim.id, claim.is_public)"
              :disabled="claim.status !== 'approved'"
            />
            <span class="privacy-tip" v-if="claim.status !== 'approved'">
              （只有已批准的认领记录可以公开）
            </span>
          </div>
          <el-button type="primary" size="small" @click="goToItem(claim.item_id)">
            查看物品详情
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Trophy, Refresh, Clock, Edit } from '@element-plus/icons-vue'
import request from '../utils/request'
import { absoluteUrl } from '../utils/request'

const router = useRouter()
const loading = ref(false)
const claims = ref([])
const filters = ref({
  status: ''
})

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

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

// 加载认领记录
const loadClaims = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.status) {
      params.status = filters.value.status
    }
    claims.value = await request.get('/my-claims', { params })
  } catch (error) {
    console.error('加载认领记录失败:', error)
    ElMessage.error('加载认领记录失败')
  } finally {
    loading.value = false
  }
}

// 切换公开状态
const togglePublic = async (claimId, isPublic) => {
  try {
    await request.put(`/claims/${claimId}/public`, {
      is_public: isPublic
    })
    ElMessage.success(isPublic ? '已设置为公开' : '已设置为隐藏')
  } catch (error) {
    console.error('切换公开状态失败:', error)
    ElMessage.error('操作失败')
    // 恢复原状态
    const claim = claims.value.find(c => c.id === claimId)
    if (claim) {
      claim.is_public = !isPublic
    }
  }
}

// 跳转到物品详情
const goToItem = (itemId) => {
  router.push(`/item/${itemId}`)
}

onMounted(() => {
  loadClaims()
})
</script>

<style scoped>
.my-claims-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.header-card {
  margin-bottom: 1.5rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.header-card h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
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
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.item-title-link {
  margin: 0;
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

.claim-content {
  margin-bottom: 1rem;
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

.claim-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.claim-time {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.claim-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: var(--border-width) solid var(--border-color);
}

.claim-privacy {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.privacy-tip {
  font-size: 0.85rem;
  color: var(--text-secondary);
}
</style>
