<template>
  <div id="app">
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <!-- Logo和标题 -->
          <div class="logo-section" @click="goHome">
            <el-icon :size="32"><Compass /></el-icon>
            <span class="app-title">校园失物招领</span>
          </div>

          <!-- 导航菜单 -->
          <el-menu
            v-if="isLoggedIn"
            mode="horizontal"
            :default-active="activeMenu"
            class="nav-menu"
            @select="handleMenuSelect"
          >
            <el-menu-item index="/">首页</el-menu-item>
            <el-menu-item index="/list/lost">失物</el-menu-item>
            <el-menu-item index="/list/found">拾物</el-menu-item>
            <el-menu-item index="/post">发布</el-menu-item>
            <el-menu-item index="/my-items">我的发布</el-menu-item>
            <el-menu-item index="/my-reports">我的举报</el-menu-item>
          </el-menu>

          <div class="search-section">
            <el-input
              v-model="keyword"
              placeholder="搜索物品关键词"
              clearable
              class="search-input"
              @keyup.enter="doSearch"
            >
              <template #append>
                <el-button @click="doSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>

          <!-- 用户区域 -->
          <div class="user-section">
            <template v-if="isLoggedIn">
              <!-- 私信图标 -->
              <el-badge :value="unreadMessageCount" :hidden="unreadMessageCount === 0" class="message-badge">
                <el-button circle @click="goToMessages">
                  <el-icon><ChatDotRound /></el-icon>
                </el-button>
              </el-badge>

              <!-- 通知图标 -->
              <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
                <el-button circle @click="goToNotifications">
                  <el-icon><Bell /></el-icon>
                </el-button>
              </el-badge>

              <el-button circle @click="toggleDarkMode">
                <el-icon v-if="!darkMode"><Moon /></el-icon>
                <el-icon v-else><Sunny /></el-icon>
              </el-button>

              <!-- 用户下拉菜单 -->
              <el-dropdown @command="handleCommand">
                <el-button>
                  <el-icon><User /></el-icon>
                  {{ user?.username }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                    <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>

            <template v-else>
              <el-button circle @click="toggleDarkMode">
                <el-icon v-if="!darkMode"><Moon /></el-icon>
                <el-icon v-else><Sunny /></el-icon>
              </el-button>
              <el-button @click="goToLogin">登录</el-button>
              <el-button type="primary" @click="goToRegister">注册</el-button>
            </template>
          </div>
        </div>
      </el-header>

      <!-- 主要内容区域 -->
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isLoggedIn, getUser, removeToken } from './utils/auth'
import { Compass, User, Bell, ArrowDown, ChatDotRound, Search, Moon, Sunny } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from './utils/request'

const router = useRouter()
const route = useRoute()

const user = ref(null)
const unreadCount = ref(0)
const unreadMessageCount = ref(0) // 新增：未读私信数
const keyword = ref('')
const darkMode = ref(false)

// 活动菜单项
const activeMenu = computed(() => {
  return route.path
})

// 加载用户信息
const loadUser = () => {
  if (isLoggedIn()) {
    user.value = getUser()
  }
}

// 加载未读通知数量
const loadUnreadCount = async () => {
  if (isLoggedIn()) {
    try {
      const data = await request.get('/notifications/unread-count')
      unreadCount.value = data.count
    } catch (error) {
      console.error('加载未读通知失败:', error)
    }
  }
}

// 加载未读私信数量
const loadUnreadMessageCount = async () => {
  if (isLoggedIn()) {
    try {
      const data = await request.get('/messages/unread-count')
      unreadMessageCount.value = data.count
    } catch (error) {
      console.error('加载未读私信失败:', error)
    }
  }
}

// 菜单选择
const handleMenuSelect = (index) => {
  router.push(index)
}

// 用户下拉菜单
const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    removeToken()
    user.value = null
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

// 导航方法
const goHome = () => router.push('/')
const goToLogin = () => router.push('/login')
const goToRegister = () => router.push('/register')
const goToNotifications = () => router.push('/notifications')
const goToMessages = () => router.push('/messages') 
const doSearch = () => {
  const q = keyword.value.trim()
  if (!q) return
  if (route.name === 'list' && route.params.category) {
    router.push({ name: 'list', params: { category: route.params.category }, query: { search: q } })
  } else {
    router.push({ name: 'list', params: { category: 'lost' }, query: { search: q } })
  }
}
const toggleDarkMode = () => {
  darkMode.value = !darkMode.value
  const b = document.body
  const h = document.documentElement
  if (darkMode.value) {
    b.classList.add('dark')
    h.classList.add('dark')
  } else {
    b.classList.remove('dark')
    h.classList.remove('dark')
  }
  localStorage.setItem('theme', darkMode.value ? 'dark' : 'light')
}

// 监听路由变化
watch(() => route.path, () => {
  loadUser()
  loadUnreadCount()
  loadUnreadMessageCount() 
})

onMounted(() => {
  loadUser()
  if (isLoggedIn()) {
    loadUnreadCount()
    loadUnreadMessageCount() 
    
    // 每30秒刷新一次未读数量
    setInterval(() => {
      loadUnreadCount()
      loadUnreadMessageCount() 
    }, 30000)
  }
  const saved = localStorage.getItem('theme')
  darkMode.value = saved === 'dark'
  const b = document.body
  const h = document.documentElement
  if (darkMode.value) {
    b.classList.add('dark')
    h.classList.add('dark')
  } else {
    b.classList.remove('dark')
    h.classList.remove('dark')
  }
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  background-color: var(--bg-page);
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  height: 60px;
  line-height: 60px;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: opacity 0.3s;
}

.logo-section:hover {
  opacity: 0.8;
}

.app-title {
  font-size: 20px;
  font-weight: bold;
}

.nav-menu {
  flex: 1;
  margin: 0 40px;
  background: transparent;
  border: none;
}

.nav-menu :deep(.el-menu-item) {
  color: white;
  border-bottom: 2px solid transparent;
}

.nav-menu :deep(.el-menu-item:hover),
.nav-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.1);
  border-bottom-color: white;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.search-section {
  flex: 0 0 360px;
}

.search-input :deep(.el-input__inner) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.search-input :deep(.el-input-group__append) {
  background: rgba(255, 255, 255, 0.2);
  border: none;
}

.message-badge,
.notification-badge {
  display: flex;
  align-items: center;
}

.message-badge :deep(.el-badge__content),
.notification-badge :deep(.el-badge__content) {
  background-color: #f56c6c;
}

.user-section .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
}

.user-section .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.app-main {
  padding: 0;
  min-height: calc(100vh - 60px);
}
</style>
