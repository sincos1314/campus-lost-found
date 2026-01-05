<template>
  <div class="list-container gradient-bg">
    <el-card class="filter-card" shadow="never">
      <el-row :gutter="15">
        <el-col :xs="24" :sm="12" :md="8">
          <el-input
            v-model="filters.search"
            placeholder="搜索标题或描述..."
            clearable
            @input="loadItems"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>

        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filters.item_type"
            placeholder="物品类型"
            clearable
            @change="loadItems"
          >
            <el-option label="全部类型" value="" />
            <el-option label="手机" value="手机" />
            <el-option label="钱包" value="钱包" />
            <el-option label="钥匙" value="钥匙" />
            <el-option label="身份证/学生证" value="身份证/学生证" />
            <el-option label="书籍" value="书籍" />
            <el-option label="衣物" value="衣物" />
            <el-option label="电子产品" value="电子产品" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-col>

        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filters.status"
            placeholder="状态"
            @change="loadItems"
          >
            <el-option label="进行中" value="open" />
            <el-option label="已解决" value="closed" />
            <el-option label="全部状态" value="" />
          </el-select>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <div class="action-buttons">
            <el-button type="primary" @click="loadItems">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
            <el-button @click="handleExport" v-if="isLoggedIn()">
              <el-icon><Download /></el-icon> 导出数据
            </el-button>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="onDateChange"
          />
        </el-col>
      </el-row>
    </el-card>

    <div class="list-header">
      <h2>
        <el-icon><List /></el-icon>
        {{ title }} ({{ total }})
      </h2>
    </div>

    <el-empty v-if="!loading && items.length === 0" description="暂无数据" />

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
          class="item-card card-glass hover-rise fade-in-up"
          shadow="hover"
          @click="goToDetail(item.id)"
        >
          <div class="item-image">
            <img
              v-if="getItemImageUrl(item)"
              :src="absoluteUrl(getItemImageUrl(item))"
              class="image-zoom"
            />
            <div v-else class="no-image">
              <el-icon :size="50"><Picture /></el-icon>
              <span>暂无图片</span>
            </div>
          </div>

          <div class="item-header">
            <el-tag
              :type="item.category === 'lost' ? 'danger' : 'success'"
              size="small"
            >
              {{ item.item_type }}
            </el-tag>
            <el-tag
              :type="item.status === 'open' ? 'success' : 'info'"
              size="small"
            >
              {{ item.status === "open" ? "进行中" : "已解决" }}
            </el-tag>
          </div>

          <h3 class="item-title">{{ item.title }}</h3>
          <p class="item-description">{{ item.description }}</p>

          <div class="item-meta">
            <div class="meta-item">
              <el-icon><Location /></el-icon>
              <span>{{ item.location }}</span>
            </div>
            <div class="meta-item">
              <el-icon><Calendar /></el-icon>
              <span>{{ item.date }}</span>
            </div>
          </div>

          <div class="item-footer">
            <div class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ item.username }}</span>
            </div>
            <el-button type="primary" size="small" link>
              查看详情 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <div v-if="!loading && total > 0" class="pagination-bar">
      <el-pagination
        background
        layout="prev, pager, next"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import request, { absoluteUrl } from "../utils/request";
import { isLoggedIn } from "../utils/auth";

const router = useRouter();
const route = useRoute();

const items = ref([]);
const loading = ref(false);
const total = ref(0);
const page = ref(1);
const pageSize = ref(8);
const filters = ref({
  search: "",
  item_type: "",
  status: "open",
  dateRange: null,
});

const category = computed(() => route.params.category);
const title = computed(() =>
  category.value === "lost" ? "失物信息列表" : "拾物信息列表"
);

const loadItems = async () => {
  loading.value = true;
  try {
    const params = {
      category: category.value,
      search: filters.value.search,
      item_type: filters.value.item_type,
      status: filters.value.status,
      page: page.value,
      page_size: pageSize.value,
    };
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.start_date = filters.value.dateRange[0];
      params.end_date = filters.value.dateRange[1];
    }
    const res = await request.get("/items", { params });
    items.value = res.items || [];
    total.value = res.total || 0;
    
    // 调试：检查返回的数据
    if (items.value.length > 0) {
      console.log('[DEBUG] 第一个物品数据:', items.value[0])
      console.log('[DEBUG] image_url:', items.value[0].image_url)
      console.log('[DEBUG] image_urls:', items.value[0].image_urls)
    }
  } catch (error) {
    console.error("加载数据失败:", error);
  } finally {
    loading.value = false;
  }
};

const goToDetail = (id) => {
  router.push(`/item/${id}`);
};

// 获取物品的图片URL（支持多张图片）
const getItemImageUrl = (item) => {
  // 优先使用 image_urls（多张图片）
  if (item.image_urls && Array.isArray(item.image_urls) && item.image_urls.length > 0) {
    return item.image_urls[0]
  }
  // 向后兼容：使用 image_url
  return item.image_url || null
}

const handleExport = async () => {
  try {
    const response = await request.get("/export", {
      params: { category: category.value },
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([response]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `失物招领数据_${new Date().toISOString().split("T")[0]}.xlsx`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    ElMessage.success("导出成功！");
  } catch (error) {
    ElMessage.error("导出失败");
    console.error("导出失败:", error);
  }
};

watch(
  () => route.params.category,
  () => {
    page.value = 1;
    loadItems();
  }
);

// 监听搜索参数变化（来自顶部全局搜索）
watch(
  () => route.query.search,
  (q) => {
    if (typeof q === "string") {
      filters.value.search = q;
      loadItems();
    }
  }
);

onMounted(() => {
  // 初始化来自路由的搜索参数
  if (typeof route.query.search === "string") {
    filters.value.search = route.query.search;
  }
  loadItems();
});

const onPageChange = (p) => {
  page.value = p;
  loadItems();
};

const onDateChange = () => {
  page.value = 1;
  loadItems();
};
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

/* 移除 Element Plus 默认的输入框包装器样式 */
.filter-card :deep(.el-input),
.filter-card :deep(.el-select),
.filter-card :deep(.el-date-editor) {
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

/* 日期范围选择器 - 仿照 textarea 的样式，只在外层有边框 */
/* el-date-editor.el-range-editor 本身是外层容器，应该有边框（仿照 textarea__inner） */
.filter-card :deep(.el-date-editor.el-range-editor) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0 !important;
}

/* 日期范围选择器内部的输入框完全透明，没有任何边框、背景、阴影 - 加强规则 */
.filter-card :deep(.el-date-editor.el-range-editor .el-input),
.filter-card :deep(.el-date-editor.el-range-editor .el-input.is-focus),
.filter-card :deep(.el-date-editor.el-range-editor .el-input:hover),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__wrapper),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__wrapper.is-focus),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__wrapper:hover),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__wrapper.is-disabled),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__wrapper.is-active) {
  border: none !important;
  border-width: 0 !important;
  box-shadow: none !important;
  background: transparent !important;
  background-color: transparent !important;
  padding: 0.6rem 1rem !important;
}

/* 日期范围选择器内部的所有元素完全透明 - 覆盖所有可能的状态 */
.filter-card :deep(.el-date-editor.el-range-editor .el-input__inner),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__inner:focus),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__inner:hover),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__inner.is-disabled),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__prefix),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__prefix-inner),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__suffix),
.filter-card :deep(.el-date-editor.el-range-editor .el-input__suffix-inner),
.filter-card :deep(.el-date-editor.el-range-editor .el-range-separator),
.filter-card :deep(.el-date-editor.el-range-editor .el-range-input),
.filter-card :deep(.el-date-editor.el-range-editor .el-range-input__inner) {
  border: none !important;
  border-width: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

/* 焦点状态的硬阴影（只在外层） */
.filter-card :deep(.el-date-editor.el-range-editor.is-focus),
.filter-card :deep(.el-date-editor.el-range-editor:focus-within) {
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
  color: white;
}

.filter-card :deep(.el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.filter-card :deep(.el-button:active) {
  transform: translateY(0) translateX(0);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.list-header {
  margin-bottom: 2rem;
}

.list-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text);
  font-size: 2rem;
  font-weight: 900;
}

.item-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  overflow: hidden;
}

.item-card:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.item-image {
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  border-radius: calc(var(--border-radius) - 2px);
  border: var(--border-width) solid var(--border-color);
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #909399;
}

.item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.item-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-description {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding-top: 12px;
  border-top: var(--border-width) solid var(--border-color);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--text-secondary);
}

.item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: var(--border-width) solid var(--border-color);
}

.item-footer :deep(.el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  font-weight: 700;
  background: var(--color-accent);
  color: white !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.item-footer :deep(.el-button:hover) {
  background: var(--color-accent) !important;
  color: white !important;
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--text-secondary);
}

.skeleton-bg {
  background: var(--color-primary);
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
</style>
