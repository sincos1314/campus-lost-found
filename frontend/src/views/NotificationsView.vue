<template>
  <div class="notifications-container">
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <h2>
          <el-icon><Bell /></el-icon>
          消息通知
          <el-badge :value="unreadCount" v-if="unreadCount > 0" />
        </h2>
        <el-button
          type="primary"
          @click="markAllRead"
          :disabled="unreadCount === 0"
        >
          全部标记为已读
        </el-button>
      </div>
    </el-card>

    <el-empty v-if="notifications.length === 0" description="暂无通知" />

    <el-card
      v-else
      v-for="notification in notifications"
      :key="notification.id"
      class="notification-card"
      :class="{ unread: !notification.is_read }"
      shadow="hover"
      @click="handleNotificationClick(notification)"
    >
      <div class="notification-content">
        <div class="notification-icon">
          <el-icon
            :size="30"
            :color="getIconColor(notification.type)"
          >
            <component :is="getIconComponent(notification.type)" />
          </el-icon>
        </div>
        
        <div class="notification-body">
          <div class="notification-header">
            <h3>{{ notification.title }}</h3>
            <el-tag
              :type="getTagType(notification.type)"
              size="small"
            >
              {{ getTypeLabel(notification.type) }}
            </el-tag>
          </div>
          <p>{{ notification.content }}</p>
          <div class="notification-footer">
            <span class="time">{{ notification.created_at }}</span>
            <el-button
              v-if="notification.related_item_id"
              type="primary"
              size="small"
              link
            >
              查看详情
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="notification-status">
          <el-icon v-if="!notification.is_read" color="#409EFF" :size="20">
            <CircleFilled />
          </el-icon>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { InfoFilled, SuccessFilled, WarningFilled } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const notifications = ref([])

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

const loadNotifications = async () => {
  try {
    notifications.value = await request.get('/notifications')
  } catch (error) {
    console.error('加载通知失败:', error)
  }
}

const handleNotificationClick = async (notification) => {
  // 标记为已读
  if (!notification.is_read) {
    try {
      await request.put(`/notifications/${notification.id}/read`)
      notification.is_read = true
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }

  // 如果有关联物品，跳转到详情页
  if (notification.related_item_id) {
    router.push(`/item/${notification.related_item_id}`)
  }
}

const markAllRead = async () => {
  try {
    await request.put('/notifications/mark-all-read')
    notifications.value.forEach(n => n.is_read = true)
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    console.error('操作失败:', error)
  }
}

const getIconComponent = (type) => {
  const icons = {
    info: InfoFilled,
    success: SuccessFilled,
    warning: WarningFilled
  }
  return icons[type] || InfoFilled
}

const getIconColor = (type) => {
  const colors = {
    info: '#409EFF',
    success: '#67C23A',
    warning: '#E6A23C'
  }
  return colors[type] || '#409EFF'
}

const getTagType = (type) => {
  const types = {
    info: 'info',
    success: 'success',
    warning: 'warning'
  }
  return types[type] || 'info'
}

const getTypeLabel = (type) => {
  const labels = {
    info: '通知',
    success: '成功',
    warning: '提醒'
  }
  return labels[type] || '通知'
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.notifications-container {
  max-width: 900px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
  border-radius: 10px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  color: #333;
}

.notification-card {
  margin-bottom: 15px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.notification-card.unread {
  background: #f0f9ff;
  border-left: 4px solid #409EFF;
}

.notification-card:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.notification-content {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}

.notification-icon {
  flex-shrink: 0;
}

.notification-body {
  flex: 1;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.notification-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
}

.notification-body p {
  color: #666;
  line-height: 1.6;
  margin-bottom: 10px;
}

.notification-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time {
  font-size: 13px;
  color: #909399;
}

.notification-footer :deep(.el-button--primary.is-link) {
  color: #409EFF !important;
  font-weight: 600;
}

.notification-footer :deep(.el-button--primary.is-link:hover) {
  color: #66b1ff !important;
}

.notification-status {
  flex-shrink: 0;
}
</style>
