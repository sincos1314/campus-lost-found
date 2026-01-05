<template>
  <div class="list-container">
    <el-card class="filter-card" shadow="never">
      <el-row :gutter="15">
        <el-col :xs="12" :sm="6" :md="4">
          <el-select v-model="filters.category" placeholder="类型" @change="loadItems">
            <el-option label="全部" value="" />
            <el-option label="失物" value="lost" />
            <el-option label="拾物" value="found" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="6" :md="4">
          <el-select v-model="filters.status" placeholder="状态" @change="loadItems">
            <el-option label="全部状态" value="" />
            <el-option label="进行中" value="open" />
            <el-option label="已解决" value="closed" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <div class="action-buttons">
            <el-button type="primary" @click="loadItems"><el-icon><Refresh /></el-icon> 刷新</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <div class="list-header">
      <h2>
        <el-icon><User /></el-icon>
        发布者历史 ({{ total }})
      </h2>
    </div>

    <el-empty v-if="!loading && items.length === 0" :description="emptyText" />

    <el-row :gutter="20" v-else>
      <el-col v-for="item in items" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="item-card" shadow="hover" @click="goToDetail(item.id)">
          <div class="item-image">
            <img v-if="getItemImageUrl(item)" :src="absoluteUrl(getItemImageUrl(item))" />
            <div v-else class="no-image">
              <el-icon :size="50"><Picture /></el-icon>
              <span>暂无图片</span>
            </div>
          </div>
          <h3 class="item-title">{{ item.title }}</h3>
          <div class="item-meta">
            <el-tag :type="item.category === 'lost' ? 'danger' : 'success'" size="small">
              {{ item.category === 'lost' ? '失物' : '拾物' }}
            </el-tag>
            <el-tag :type="item.status === 'open' ? 'success' : 'info'" size="small">
              {{ item.status === 'open' ? '进行中' : '已解决' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="!loading && total > 0" class="pagination-bar">
      <el-pagination background layout="prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPageChange" />
    </div>
  </div>
  </template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request, { absoluteUrl, previewList } from '../utils/request'
import { getToken } from '../utils/auth'
import { Refresh, Picture, User } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userId = parseInt(route.params.id)

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(8)
const loading = ref(false)
const emptyText = ref('暂无数据')
const filters = ref({ category: '', status: '' })

const loadItems = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value, category: filters.value.category, status: filters.value.status, token: getToken() }
    const res = await request.get(`/users/${userId}/items`, { params })
    if (res.message) {
      emptyText.value = res.message
      items.value = []
      total.value = 0
    } else {
      items.value = res.items || []
      total.value = res.total || 0
    }
  } finally {
    loading.value = false
  }
}

const onPageChange = (p) => { page.value = p; loadItems() }
const goToDetail = (id) => router.push(`/item/${id}`)

// 获取物品的图片URL（支持多张图片）
const getItemImageUrl = (item) => {
  // 优先使用 image_urls（多张图片）
  if (item.image_urls && Array.isArray(item.image_urls) && item.image_urls.length > 0) {
    return item.image_urls[0]
  }
  // 向后兼容：使用 image_url
  return item.image_url || null
}

loadItems()
</script>

<style scoped>
.list-container { 
  max-width: 1400px; 
  margin: 0 auto; 
  padding: 2rem;
}

.filter-card { 
  margin-bottom: 2rem; 
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 1.5rem;
}

.action-buttons { display: flex; gap: 10px; }
.list-header { margin-bottom: 20px; }
.list-header h2 {
  font-size: 2rem;
  font-weight: 900;
  color: var(--color-text);
}

.item-card { 
  margin-bottom: 20px; 
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  overflow: hidden; 
  cursor: pointer; 
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.item-card:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.item-image { 
  width: 100%; 
  height: 180px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  background: var(--color-primary);
  border-bottom: var(--border-width) solid var(--border-color);
}

.item-image img { width: 100%; height: 100%; object-fit: cover; }
.item-title { font-size: 16px; font-weight: 700; margin: 10px 0; color: var(--color-text); padding: 0 1rem; }
.item-meta { display: flex; gap: 8px; padding: 0 1rem 1rem; }
.no-image { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-secondary); }
.pagination-bar { display: flex; justify-content: center; padding: 20px 0; }

/* 移除 Element Plus 默认的输入框包装器样式 */
.filter-card :deep(.el-input),
.filter-card :deep(.el-select) {
  border: none !important;
  box-shadow: none !important;
}

.filter-card :deep(.el-input__wrapper),
.filter-card :deep(.el-select__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

.filter-card :deep(.el-input__inner),
.filter-card :deep(.el-select__placeholder),
.filter-card :deep(.el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.filter-card :deep(.el-input__wrapper.is-focus),
.filter-card :deep(.el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.filter-card :deep(.el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.filter-card :deep(.el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

.filter-card :deep(.el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}
</style>
