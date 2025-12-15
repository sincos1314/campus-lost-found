<template>
  <div class="item-detail-container">
    <!-- 返回按钮 -->
    <el-button class="back-button" @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      返回列表
    </el-button>

    <el-card class="detail-card" v-loading="loading">
      <el-row :gutter="40">
        <!-- 左侧：图片 -->
        <el-col :xs="24" :sm="24" :md="10">
          <div class="image-section">
            <el-image
              v-if="item.image_url"
              :src="fullImageUrl"
              :preview-src-list="previewList(item.image_url)"
              fit="cover"
              class="item-image"
            >
              <template #error>
                <div class="image-placeholder">
                  <el-icon :size="60"><Picture /></el-icon>
                  <p>暂无图片</p>
                </div>
              </template>
            </el-image>
            <div v-else class="image-placeholder">
              <el-icon :size="60"><Picture /></el-icon>
              <p>暂无图片</p>
            </div>
          </div>
        </el-col>

        <!-- 右侧：详细信息 -->
        <el-col :xs="24" :sm="24" :md="14">
          <div class="info-section">
            <!-- 标题和标签 -->
            <div class="title-section">
              <h2>{{ item.title }}</h2>
              <div class="tags">
                <el-tag
                  :type="item.category === 'lost' ? 'danger' : 'success'"
                  size="large"
                >
                  {{ item.category === "lost" ? "失物" : "拾物" }}
                </el-tag>
                <el-tag
                  :type="item.status === 'open' ? 'info' : 'warning'"
                  size="large"
                >
                  {{ item.status === "open" ? "进行中" : "已解决" }}
                </el-tag>
              </div>
            </div>

            <!-- 详细信息表格 -->
            <el-descriptions :column="1" border class="info-table">
              <el-descriptions-item label="物品类型">
                {{ item.item_type }}
              </el-descriptions-item>
              <el-descriptions-item label="地点">
                <el-icon><Location /></el-icon>
                {{ item.location }}
              </el-descriptions-item>
              <el-descriptions-item label="日期">
                <el-icon><Calendar /></el-icon>
                {{ item.date }}
              </el-descriptions-item>
              <el-descriptions-item label="发布时间">
                <el-icon><Clock /></el-icon>
                {{ item.created_at }}
              </el-descriptions-item>
              <el-descriptions-item label="发布人">
                <el-button type="text" @click="viewPublisher">
                  <el-icon><User /></el-icon>
                  {{ item.username }}
                </el-button>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 详细描述 -->
            <div class="description-section">
              <h3>详细描述</h3>
              <p class="description-text">{{ item.description }}</p>
            </div>

            <div class="timeline-section">
              <h3>时间线</h3>
              <el-timeline>
                <el-timeline-item
                  v-for="(ev, i) in filteredTimeline"
                  :key="i"
                  :timestamp="ev.time"
                  :type="ev.type === 'success' ? 'success' : 'primary'"
                >
                  <div class="timeline-title">{{ ev.title }}</div>
                  <div class="timeline-desc">{{ ev.description }}</div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- 联系方式 -->
            <div class="contact-section">
              <h3>联系方式</h3>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="联系人">
                  {{ item.contact_name }}
                </el-descriptions-item>
                <el-descriptions-item label="联系电话">
                  <span class="phone-number">{{ item.contact_phone }}</span>
                  <el-button
                    type="primary"
                    size="small"
                    :icon="CopyDocument"
                    @click="copyPhone"
                    style="margin-left: 10px"
                  >
                    复制
                  </el-button>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 操作按钮 -->
            <div class="action-section">
              <!-- 新增：联系发布者按钮（非本人发布时显示） -->
              <el-button
                v-if="isLoggedIn() && item.user_id !== getCurrentUserId()"
                type="primary"
                size="large"
                @click="contactPublisher"
              >
                <el-icon><ChatDotRound /></el-icon>
                联系发布者
              </el-button>

              <!-- 本人发布时显示管理按钮 -->
              <template
                v-if="isLoggedIn() && item.user_id === getCurrentUserId()"
              >
                <el-button
                  v-if="item.status === 'open'"
                  type="success"
                  size="large"
                  @click="markAsSolved"
                >
                  <el-icon><Check /></el-icon>
                  标记为已解决
                </el-button>
                <el-button type="danger" size="large" @click="deleteItem">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
              <el-button type="info" size="large" @click="openShare"
                >分享链接</el-button
              >
              <el-button type="warning" size="large" @click="openReport"
                >举报</el-button
              >
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
    <el-dialog v-model="shareVisible" title="分享二维码" width="320px">
      <div class="qr-box">
        <el-image
          :src="qrUrl"
          fit="contain"
          style="width: 260px; height: 260px"
        />
      </div>
      <template #footer>
        <el-button @click="copyLink">复制链接</el-button>
        <el-button type="primary" @click="shareVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <ReportDialog
      v-model="reportVisible"
      :target-user-id="item.user_id"
      :item-id="itemId"
      @submitted="onReported"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  Picture,
  Location,
  Calendar,
  Clock,
  User,
  CopyDocument,
  Check,
  Delete,
  ChatDotRound,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import ReportDialog from "../components/ReportDialog.vue";
import request from "../utils/request";
import { isLoggedIn, getUser } from "../utils/auth";
import { absoluteUrl, previewList } from '../utils/request'

const route = useRoute();
const router = useRouter();
const itemId = route.params.id;

const item = ref({});
const loading = ref(false);
const timeline = ref([]);
const shareVisible = ref(false);
const qrUrl = ref("");
const reportVisible = ref(false);
const fullImageUrl = computed(() => item.value?.image_url ? absoluteUrl(item.value.image_url) : '')

// 过滤时间线：只显示"发布"和"物品已找回"，并修改"物品已找回"的描述
const filteredTimeline = computed(() => {
  return timeline.value.filter(ev => {
    // 只保留"发布"和"物品已找回"相关的事件
    return ev.title === '发布' || ev.title === '物品已找回'
  }).map(ev => {
    // 修改"物品已找回"的描述
    if (ev.title === '物品已找回') {
      return {
        ...ev,
        description: item.value.category === 'lost' ? '恭喜！失物已找回！' : '恭喜！拾物已被找回！'
      }
    }
    return ev
  })
})

// 获取当前用户ID
const getCurrentUserId = () => {
  const user = getUser();
  return user?.id;
};

// 加载物品详情
const loadItemDetail = async () => {
  loading.value = true;
  try {
    item.value = await request.get(`/items/${itemId}`);
    timeline.value = await request.get(`/items/${itemId}/timeline`);
  } catch (error) {
    console.error("加载详情失败:", error);
    ElMessage.error("加载失败");
  } finally {
    loading.value = false;
  }
};

// 联系发布者（新增）
const contactPublisher = async () => {
  try {
    if (isLoggedIn() && item.value.user_id === getCurrentUserId()) {
      ElMessage.warning("不能与自己创建会话");
      return;
    }
    // 获取或创建与发布者的会话
    const conversation = await request.post(
      `/conversations/${item.value.user_id}`
    );
    // 跳转到聊天页面
    router.push(`/chat/${conversation.id}`);
  } catch (error) {
    console.error("创建会话失败:", error);
    ElMessage.error("操作失败");
  }
};

// 复制电话
const copyPhone = () => {
  navigator.clipboard.writeText(item.value.contact_phone);
  ElMessage.success("电话已复制到剪贴板");
};

// 标记为已解决
const markAsSolved = async () => {
  try {
    await ElMessageBox.confirm("确定要标记为已解决吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    await request.put(`/items/${itemId}`, { status: "closed" });
    ElMessage.success("已标记为已解决");
    await loadItemDetail();
  } catch (error) {
    if (error !== "cancel") {
      console.error("操作失败:", error);
    }
  }
};

// 删除物品
const deleteItem = async () => {
  try {
    await ElMessageBox.confirm(
      "确定要删除这条信息吗？删除后无法恢复。",
      "警告",
      {
        confirmButtonText: "确定删除",
        cancelButtonText: "取消",
        type: "error",
      }
    );

    await request.delete(`/items/${itemId}`);
    ElMessage.success("删除成功");
    router.push(`/list/${item.value.category}`);
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
    }
  }
};

// 返回列表
const goBack = () => {
  router.back();
};

onMounted(() => {
  loadItemDetail();
});

const copyLink = () => {
  const url = window.location.href;
  navigator.clipboard.writeText(url);
  ElMessage.success("链接已复制到剪贴板");
};

const openShare = () => {
  shareVisible.value = true;
  const url = window.location.href;
  qrUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=260x260&data=${encodeURIComponent(
    url
  )}`;
};

const viewPublisher = () => {
  if (item.value.user_id) {
    router.push(`/user/${item.value.user_id}/items`);
  }
};

const openReport = () => {
  reportVisible.value = true;
};
const onReported = () => {
  ElMessage.success("举报已提交");
};
</script>

<style scoped>
.item-detail-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.back-button {
  margin-bottom: 2rem;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.back-button:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.detail-card {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 2rem;
}

.image-section {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--border-radius);
  overflow: hidden;
  border: var(--border-width) solid var(--border-color);
}

.item-image {
  width: 100%;
  height: 100%;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--color-primary);
  color: var(--text-secondary);
}

.info-section {
  padding: 20px 0;
}

.title-section {
  margin-bottom: 30px;
}

.title-section h2 {
  font-size: 2rem;
  font-weight: 900;
  margin: 0 0 15px 0;
  color: var(--color-text);
}

.tags {
  display: flex;
  gap: 10px;
}

.info-table {
  margin-bottom: 30px;
}

.description-section,
.contact-section {
  margin-bottom: 30px;
}

.timeline-section {
  margin-bottom: 30px;
}

.timeline-title {
  font-weight: 600;
}

.timeline-desc {
  color: var(--text-secondary);
}

.qr-box {
  display: flex;
  justify-content: center;
  align-items: center;
}

.description-section h3,
.contact-section h3 {
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 15px;
  color: var(--color-text);
}

.description-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
  background-color: var(--color-primary);
  padding: 1rem;
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}

.phone-number {
  font-size: 16px;
  font-weight: bold;
  color: #409eff;
}

.action-section {
  display: flex;
  gap: 15px;
  padding-top: 20px;
  border-top: var(--border-width) solid var(--border-color);
  flex-wrap: wrap;
}

.action-section .el-button {
  flex: 1;
  max-width: 200px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.action-section .el-button:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.action-section .el-button:active {
  transform: translateY(0) translateX(0);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .image-section {
    margin-bottom: 20px;
  }

  .action-section {
    flex-direction: column;
  }

  .action-section .el-button {
    max-width: 100%;
  }
}

/* 对话框中的输入框样式 */
.item-detail-container :deep(.el-dialog) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.item-detail-container :deep(.el-dialog .el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.item-detail-container :deep(.el-dialog .el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

.item-detail-container :deep(.el-dialog .el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}
</style>
