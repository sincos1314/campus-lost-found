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
              v-if="item.image_url"
              :src="absoluteUrl(item.image_url)"
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
  } catch (error) {
    console.error("加载数据失败:", error);
  } finally {
    loading.value = false;
  }
};

const goToDetail = (id) => {
  router.push(`/item/${id}`);
};

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
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 10px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.list-header {
  margin-bottom: 20px;
}

.list-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
  font-size: 24px;
}

.item-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 10px;
  overflow: hidden;
}

.item-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.item-image {
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: var(--bg-page);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  border-radius: 8px;
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
  font-weight: 600;
  color: var(--text-primary);
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
  border-top: 1px solid #eee;
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
  border-top: 1px solid #eee;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--text-secondary);
}

.skeleton-bg {
  background: var(--bg-page);
}

.pagination-bar {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style>
