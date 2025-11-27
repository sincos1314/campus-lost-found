<template>
  <div class="messages-container">
    <el-card class="messages-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><ChatDotRound /></el-icon>
            私信列表
          </span>
          <div class="actions">
            <el-badge :value="totalUnread" :hidden="totalUnread === 0" class="unread-badge">
              <el-button type="primary" size="small" @click="loadConversations">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </el-badge>
            <el-button v-if="me?.is_banned" type="warning" size="small" @click="contactBanAdmin" style="margin-left:8px">联系封禁管理员</el-button>
          </div>
        </div>
      </template>

      <el-empty v-if="conversations.length === 0" description="暂无私信" />

      <div v-else class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          @click="openChat(conv)"
        >
          <el-avatar :size="50" class="avatar">
            {{ conv.other_user.username.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="conversation-info">
            <div class="top-line">
              <span class="username">
                {{ conv.other_user.username }}
                <el-tag v-if="conv.other_user.role==='admin'" type="success" size="small" style="margin-left:6px">{{ levelText(conv.other_user.admin_level) }}</el-tag>
              </span>
              <span class="time">{{ formatTime(conv.last_message_time) }}</span>
            </div>
            <div class="bottom-line">
              <span class="last-message">{{ conv.last_message || '暂无消息' }}</span>
              <el-badge
                v-if="conv.unread_count > 0"
                :value="conv.unread_count"
                class="unread-count"
              />
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Refresh } from '@element-plus/icons-vue'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import { getUser } from '../utils/auth'

const router = useRouter()
const conversations = ref([])
const me = getUser()
const levelText = (l) => ({ low:'低级', mid:'中级', high:'高级' }[l] || '管理员')

// 计算未读总数
const totalUnread = computed(() => {
  return conversations.value.reduce((sum, conv) => sum + conv.unread_count, 0)
})

// 加载会话列表
const loadConversations = async () => {
  try {
    conversations.value = await request.get('/conversations')
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 打开聊天窗口
const openChat = (conv) => {
  router.push(`/chat/${conv.id}`)
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString()
}

onMounted(() => {
  loadConversations()
  // 每30秒刷新一次
  setInterval(loadConversations, 30000)
})

const contactBanAdmin = async () => {
  try {
    let bannedBy = me?.banned_by
    if (!bannedBy) {
      const profile = await request.get('/auth/profile')
      bannedBy = profile.banned_by
    }
    if (!bannedBy) {
      ElMessage.error('未找到封禁管理员')
      return
    }
    const conv = await request.get(`/conversations/${bannedBy}`)
    router.push(`/chat/${conv.id}`)
  } catch (e) {
    console.error(e)
    ElMessage.error('无法联系封禁管理员')
  }
}
</script>

<style scoped>
.messages-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
}

.messages-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 15px;
  cursor: pointer;
  transition: background-color 0.3s;
  border-bottom: 1px solid #f0f0f0;
}

.conversation-item:hover {
  background-color: #f5f7fa;
}

.conversation-item:last-child {
  border-bottom: none;
}

.avatar {
  flex-shrink: 0;
  margin-right: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: bold;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.top-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.username {
  font-weight: bold;
  font-size: 16px;
  color: #303133;
}

.time {
  font-size: 12px;
  color: #909399;
}

.bottom-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-message {
  flex: 1;
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unread-count {
  margin-left: 10px;
}
</style>
