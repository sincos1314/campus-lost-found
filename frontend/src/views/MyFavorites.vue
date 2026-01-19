<template>
  <div class="favorites-container gradient-bg">
    <el-card class="header-card">
      <div class="header-content">
        <h1>
          <el-icon><Star /></el-icon>
          我的收藏
        </h1>
        <p class="subtitle">共收藏了 {{ total }} 件物品</p>
      </div>
    </el-card>

    <el-empty v-if="!loading && items.length === 0" description="暂无收藏" :image-size="150" />

    <el-row :gutter="20" v-if="loading">
      <el-col v-for="n in 8" :key="n" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="item-card" shadow="never">
          <el-skeleton animated :rows="4">
            <template #template>
              <div class="item-image skeleton-bg" />
              <el-skeleton-item
                variant="p"
                style="margin: 10px 0; height: 16px"
              />
              <el-skeleton-item
                variant="p"
                style="margin: 6px 0; height: 12px"
              />
            </template>
          </el-skeleton>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-else>
      <el-col
        v-for="item in items"
        :key="item.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
      >
        <el-card
          class="item-card"
          shadow="hover"
          @click="goToDetail(item.id)"
        >
          <div class="item-image-container">
            <el-image
              v-if="item.image_url"
              :src="absoluteUrl(item.image_url)"
              fit="cover"
              class="item-image"
            >
              <template #error>
                <div class="image-placeholder">
                  <el-icon :size="40"><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div v-else class="image-placeholder">
              <el-icon :size="40"><Picture /></el-icon>
            </div>
            <div class="item-status-badge">
              <el-tag
                :type="item.status === 'open' ? 'info' : 'warning'"
                size="small"
              >
                {{ item.status === 'open' ? '进行中' : '已解决' }}
              </el-tag>
            </div>
          </div>
          <div class="item-info">
            <h3 class="item-title">{{ item.title }}</h3>
            <div class="item-meta">
              <el-tag
                :type="item.category === 'lost' ? 'danger' : 'success'"
                size="small"
              >
                {{ item.category === 'lost' ? '失物' : '拾物' }}
              </el-tag>
              <span class="item-type">{{ item.item_type }}</span>
            </div>
            <div class="item-location">
              <el-icon><Location /></el-icon>
              {{ item.location }}
            </div>
            <div class="item-time">{{ item.created_at }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页 -->
    <div v-if="!loading && total > 0" class="pagination-bar">
      <el-pagination
        background
        layout="prev, pager, next"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Star, Picture, Location } from '@element-plus/icons-vue'
import request from '../utils/request'
import { absoluteUrl } from '../utils/request'

const router = useRouter()

const items = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(8)

const loadFavorites = async () => {
  loading.value = true
  try {
    const data = await request.get('/my-favorites', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    items.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    console.error('加载收藏失败:', error)
  } finally {
    loading.value = false
  }
}

const onPageChange = (page) => {
  currentPage.value = page
  loadFavorites()
}

const goToDetail = (itemId) => {
  router.push(`/item/${itemId}`)
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-container {
  max-width: 1400px;
  margin: 2rem auto;
  padding: 0 2rem;
  min-height: calc(100vh - 200px);
}

.header-card {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  margin-bottom: 2rem;
}

.header-content {
  text-align: center;
  padding: 1rem;
}

.header-content h1 {
  font-size: 2rem;
  font-weight: 900;
  margin: 0 0 0.5rem 0;
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  margin: 0;
}

.item-card {
  margin-bottom: 2rem;
  cursor: pointer;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.item-card:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.item-image-container {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: var(--border-radius);
  margin-bottom: 1rem;
}

.item-image {
  width: 100%;
  height: 100%;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--text-secondary);
}

.item-status-badge {
  position: absolute;
  top: 10px;
  right: 10px;
}

.item-info {
  padding: 0.5rem 0;
}

.item-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.item-type {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.item-location {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.item-time {
  font-size: 0.85rem;
  color: var(--muted);
}

.skeleton-bg {
  width: 100%;
  aspect-ratio: 1;
  background: var(--color-primary);
  border-radius: var(--border-radius);
}

.pagination-bar {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.pagination-bar :deep(.el-pagination) {
  --el-pagination-button-bg-color: var(--color-card);
  --el-pagination-button-color: var(--color-text);
  --el-pagination-hover-color: var(--color-accent);
}

.pagination-bar :deep(.el-pager li) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  margin: 0 2px;
  font-weight: 600;
}

.pagination-bar :deep(.el-pagination .btn-prev),
.pagination-bar :deep(.el-pagination .btn-next) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .favorites-container {
    padding: 0 1rem;
  }

  .header-content h1 {
    font-size: 1.5rem;
  }
}
</style>
