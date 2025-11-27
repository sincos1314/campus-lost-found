<template>
  <div class="chat-container">
    <el-card class="chat-card">
      <!-- 聊天头部 -->
      <template #header>
        <div class="chat-header">
          <el-button size="small" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <span class="chat-title">
            {{ otherUser?.username }}
            <el-tag v-if="otherUser?.role==='admin'" type="success" size="small" style="margin-left:8px">{{ levelText(otherUser?.admin_level) }}</el-tag>
          </span>
          <el-button size="small" @click="loadMessages">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </template>

      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <div
          v-for="(msg, idx) in messages"
          :key="msg.id"
          :class="['message-item', msg.is_sender ? 'sent' : 'received']"
        >
          <div v-if="shouldShowDate(idx)" class="date-separator">
            {{ formatDate(msg.created_at) }}
          </div>
          <div v-if="isOtherUserTyping" class="typing-indicator">
            <span>{{ otherUser?.username }} 正在输入...</span>
            <span class="typing-dots">
              <span>.</span><span>.</span><span>.</span>
            </span>
          </div>

          <!-- 撤回的消息 -->
          <div v-if="msg.is_recalled" class="recalled-message">
            {{ msg.is_sender ? "你撤回了一条消息" : "对方撤回了一条消息" }}
          </div>

          <!-- 正常消息 -->
          <div v-else class="message-bubble">
            <!-- 文字消息 -->
            <div v-if="msg.message_type === 'text'" class="text-message">
              {{ msg.content }}
            </div>

            <!-- 图片消息 -->
            <div v-else-if="msg.message_type === 'image'" class="image-message">
              <el-image
                :src="imageUrl(msg)"
                :preview-src-list="[imageUrl(msg)]"
                fit="cover"
                class="message-image"
              />
            </div>

            <!-- 消息时间和操作 -->
            <div class="message-footer">
              <span class="message-time">{{ formatTime(msg.created_at) }}</span>
              <span v-if="msg.is_sender && msg.is_read" class="read-indicator">已读</span>
              <el-dropdown
                v-if="msg.is_sender"
                trigger="click"
                @command="handleCommand($event, msg)"
              >
                <el-icon class="message-menu"><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="recall" v-if="canRecall(msg)"
                      >撤回</el-dropdown-item
                    >
                    <el-dropdown-item command="delete">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-dropdown
                v-else
                trigger="click"
                @command="handleCommand($event, msg)"
              >
                <el-icon class="message-menu"><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="delete">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <el-upload
          :action="`http://localhost:5000/api/conversations/${conversationId}/send-image`"
          :headers="{ Authorization: `Bearer ${getToken()}` }"
          name="image"
          :show-file-list="false"
          :before-upload="beforeImageUpload"
          :on-success="handleImageSuccess"
          :on-error="handleImageError"
        >
          <el-button :icon="Picture" circle />
        </el-upload>

        <el-input
          v-model="newMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息..."
          @input="handleInput"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.ctrl.enter.exact="newMessage += '\n'"
        />

        <el-button type="primary" @click="sendMessage" :loading="sending">
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, onBeforeUnmount } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  Refresh,
  Picture,
  MoreFilled,
} from "@element-plus/icons-vue";
import request from "../utils/request";
import { getToken } from "../utils/auth";
import { ElMessage, ElMessageBox } from "element-plus";
import { io } from "socket.io-client";

const route = useRoute();
const router = useRouter();
const conversationId = parseInt(route.params.id);

const messages = ref([]);
const newMessage = ref("");
const sending = ref(false);
const messageListRef = ref(null);
const otherUser = ref(null);

const socket = ref(null);
const isConnected = ref(false);
const isOtherUserTyping = ref(false);

const levelText = (l) => ({ low: '低级', mid: '中级', high: '高级' }[l || ''] || '管理员')

// 加载会话信息
const loadConversation = async () => {
  try {
    const data = await request.get(`/conversation/${conversationId}`);
    otherUser.value = data.other_user;
  } catch (error) {
    console.error("加载会话失败:", error);
  }
};

// 加载消息列表
const loadMessages = async () => {
  try {
    messages.value = await request.get(
      `/conversations/${conversationId}/messages`
    );
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error("加载消息失败:", error);
  }
};

// 发送文字消息
const sendMessage = async () => {
  if (!newMessage.value.trim()) return;

  sending.value = true;
  try {
    await request.post(`/conversations/${conversationId}/messages`, {
      content: newMessage.value,
    });
    newMessage.value = "";
    await loadMessages();
  } catch (error) {
    console.error("发送消息失败:", error);
  } finally {
    sending.value = false;
  }
};

// 图片上传前验证
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith("image/");
  const isLt10M = file.size / 1024 / 1024 <= 10;

  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return false;
  }
  if (!isLt10M) {
    ElMessage.error("图片大小不能超过10MB！");
    return false;
  }
  return true;
};

// 图片上传成功
const handleImageSuccess = async () => {
  ElMessage.success("图片发送成功");
  await loadMessages();
};

// 图片上传失败
const handleImageError = () => {
  ElMessage.error("图片发送失败");
};

// 处理消息操作
const handleCommand = async (command, msg) => {
  if (command === "delete") {
    await deleteMessage(msg);
  } else if (command === "recall") {
    await recallMessage(msg);
  }
};

// 删除消息
const deleteMessage = async (msg) => {
  try {
    await ElMessageBox.confirm(
      "确定要删除这条消息吗？删除后仅在你这边不可见。",
      "提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    await request.delete(`/messages/${msg.id}`);
    ElMessage.success("删除成功");
    await loadMessages();
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除消息失败:", error);
    }
  }
};

// 撤回消息
const recallMessage = async (msg) => {
  try {
    await ElMessageBox.confirm(
      "确定要撤回这条消息吗？撤回后双方都无法看到。",
      "提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    await request.put(`/messages/${msg.id}/recall`);
    ElMessage.success("撤回成功");
    await loadMessages();
  } catch (error) {
    if (error !== "cancel") {
      if (error.response?.data?.message) {
        ElMessage.error(error.response.data.message);
      } else {
        console.error("撤回消息失败:", error);
      }
    }
  }
};

// 判断是否可以撤回（2分钟内）
const canRecall = (msg) => {
  const now = new Date();
  const msgTime = new Date(msg.created_at);
  const diff = (now - msgTime) / 1000; // 秒
  return diff <= 120 && !msg.is_recalled;
};

// 格式化时间
const formatTime = (timeStr) => {
  const date = new Date(timeStr);
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatDate = (timeStr) => {
  const date = new Date(timeStr);
  return date.toLocaleDateString("zh-CN");
};

const isSameDay = (a, b) => {
  const da = new Date(a);
  const db = new Date(b);
  return (
    da.getFullYear() === db.getFullYear() &&
    da.getMonth() === db.getMonth() &&
    da.getDate() === db.getDate()
  );
};

const shouldShowDate = (idx) => {
  if (idx === 0) return true;
  const prev = messages.value[idx - 1];
  const curr = messages.value[idx];
  return !isSameDay(prev.created_at, curr.created_at);
};

const imageUrl = (msg) => {
  const token = getToken();
  const base = `http://localhost:5000${msg.image_url}`;
  return `${base}?token=${encodeURIComponent(token || '')}`;
};

// 滚动到底部
const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
  }
};

// 返回列表
const goBack = () => {
  router.push("/messages");
};

// 初始化WebSocket连接
const initWebSocket = () => {
  const token = getToken();
  if (!token) return;

  // 连接WebSocket服务器
  socket.value = io("http://localhost:5000", {
    query: { token }
  });

  // 连接成功
  socket.value.on("connect", () => {
    console.log("✅ WebSocket已连接");
    isConnected.value = true;
  });

  // 断开连接
  socket.value.on("disconnect", () => {
    console.log("🔌 WebSocket已断开");
    isConnected.value = false;
  });

  // 接收新消息
  socket.value.on("new_message", (msg) => {
    console.log("📨 收到新消息:", msg);
    messages.value.push(msg);
    nextTick(() => scrollToBottom());
  });

  // 消息发送成功回调
  socket.value.on("message_sent", (msg) => {
    console.log("✅ 消息已发送:", msg);
    // 消息已经通过正常API添加，这里只是确认
  });

  // 对方正在输入
  socket.value.on("user_typing", () => {
    isOtherUserTyping.value = true;
    setTimeout(() => {
      isOtherUserTyping.value = false;
    }, 3000);
  });

  // 错误处理
  socket.value.on("error", (error) => {
    console.error("❌ WebSocket错误:", error);
    ElMessage.error("实时消息连接失败");
  });
};

// 发送正在输入状态
let typingTimer = null;
const handleInput = () => {
  if (!socket.value || !isConnected.value) return;

  clearTimeout(typingTimer);

  const other_user_id = otherUser.value?.id;
  socket.value.emit("typing", { receiver_id: other_user_id });

  typingTimer = setTimeout(() => {
    // 停止输入状态
  }, 1000);
};

onMounted(async () => {
  await loadConversation();
  await loadMessages();

  // 初始化WebSocket
  initWebSocket();
});

onBeforeUnmount(() => {
  // 断开WebSocket连接
  if (socket.value) {
    socket.value.disconnect();
  }
});
</script>

<style scoped>
.chat-container {
  height: calc(100vh - 60px);
  padding: 20px;
  display: flex;
  justify-content: center;
}

.chat-card {
  width: 100%;
  max-width: 900px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  font-size: 18px;
  font-weight: bold;
  flex: 1;
  text-align: center;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--bg-page);
}

.message-item {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.message-item.sent {
  align-items: flex-end;
}

.message-item.received {
  align-items: flex-start;
}

.recalled-message {
  font-size: 12px;
  color: #909399;
  font-style: italic;
  padding: 5px 10px;
}

.message-bubble {
  max-width: 60%;
  position: relative;
}

.text-message {
  background-color: var(--bg-card);
  padding: 12px 16px;
  border-radius: 8px;
  word-break: break-word;
  white-space: pre-wrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sent .text-message {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.image-message {
  background-color: var(--bg-card);
  padding: 4px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message-image {
  max-width: 300px;
  max-height: 300px;
  border-radius: 4px;
  cursor: pointer;
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}

.read-indicator {
  margin-left: 8px;
  color: var(--text-secondary);
}

.date-separator {
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  margin: 10px 0;
}

.message-menu {
  cursor: pointer;
  margin-left: 8px;
  transition: color 0.3s;
}

.message-menu:hover {
  color: #409eff;
}

.input-area {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 20px;
  background-color: white;
  border-top: 1px solid #e4e7ed;
}

.input-area .el-textarea {
  flex: 1;
}

.input-area .el-button {
  height: 40px;
}

.typing-indicator {
  padding: 10px 20px;
  font-size: 14px;
  color: #909399;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 5px;
}

.typing-dots span {
  animation: blink 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%,
  60%,
  100% {
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
}
</style>
const levelText = (l) => ({ low:'低级', mid:'中级', high:'高级' }[l] || '管理员')
