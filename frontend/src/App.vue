<template>
  <div id="app">
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <!-- Logo和标题 -->
          <div class="logo-section" @click="goHome">
            <div class="logo-icon">
              <el-icon :size="28"><Compass /></el-icon>
            </div>
            <span class="app-title">UniFind校园寻宝</span>
          </div>

          <!-- 移动端汉堡菜单按钮（仅小屏显示） -->
          <button type="button" class="mobile-menu-btn" aria-label="打开菜单" @click="drawerVisible = true">
            <el-icon :size="24"><Grid /></el-icon>
          </button>

          <!-- 导航菜单（桌面端显示，小屏隐藏由抽屉替代） -->
          <div class="nav-menu">
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/list/lost') }"
              @click="goToLostSquare"
            >
              <el-icon><Search /></el-icon>
              失物广场
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/list/found') }"
              @click="goToFoundSquare"
            >
              <el-icon><Present /></el-icon>
              拾物广场
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/post') }"
              @click="goToPost"
            >
              <el-icon><Plus /></el-icon>
              发布信息
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/my-items') }"
              @click="goToMyItems"
              v-if="isLoggedInComputed"
            >
              <el-icon><FolderOpened /></el-icon>
              我的发布
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/my-favorites') }"
              @click="goToMyFavorites"
              v-if="isLoggedInComputed"
            >
              <el-icon><Star /></el-icon>
              我的收藏
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/my-reports') }"
              @click="goToMyReports"
              v-if="isLoggedInComputed"
            >
              <el-icon><Warning /></el-icon>
              我的举报
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/my-claims') }"
              @click="goToMyClaims"
              v-if="isLoggedInComputed"
            >
              <el-icon><Trophy /></el-icon>
              我的认领
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/claim-management') }"
              @click="goToClaimManagement"
              v-if="isLoggedInComputed"
            >
              <el-icon><DocumentChecked /></el-icon>
              认领管理
            </button>
            <button 
              class="nav-link"
              :class="{ active: isActiveRoute('/admin') }"
              @click="goToDashboard"
              v-if="isLoggedInComputed && user?.role === 'admin'"
            >
              <el-icon><DataAnalysis /></el-icon>
              数据看板
            </button>
          </div>

          <!-- 用户区域 -->
          <div class="user-section">
            <template v-if="isLoggedInComputed">
              <!-- 私信图标 -->
              <el-badge :value="unreadMessageCount" :hidden="unreadMessageCount === 0" class="message-badge">
                <button class="icon-btn" @click="goToMessages">
                  <el-icon><ChatDotRound /></el-icon>
                </button>
              </el-badge>

              <!-- 通知图标 -->
              <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
                <button class="icon-btn" @click="goToNotifications">
                  <el-icon><Bell /></el-icon>
                </button>
              </el-badge>

              <button class="icon-btn" @click="toggleDarkMode">
                <el-icon v-if="!darkMode"><Moon /></el-icon>
                <el-icon v-else><Sunny /></el-icon>
              </button>

              <!-- 用户下拉菜单 -->
              <el-dropdown @command="handleCommand">
                <button class="user-btn">
                  <el-icon><User /></el-icon>
                  {{ user?.username }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                    <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>

            <template v-else>
              <button class="icon-btn" @click="toggleDarkMode">
                <el-icon v-if="!darkMode"><Moon /></el-icon>
                <el-icon v-else><Sunny /></el-icon>
              </button>
              <button class="nav-btn" @click="goToLogin">登录</button>
              <button class="nav-btn nav-btn-primary" @click="goToRegister">注册</button>
            </template>
          </div>
        </div>
      </el-header>

      <!-- 主要内容区域 -->
      <el-main class="app-main gradient-bg">
        <router-view />
      </el-main>

      <!-- 移动端导航抽屉（仅小屏使用） -->
      <el-drawer
        v-model="drawerVisible"
        title="菜单"
        direction="ltr"
        size="280px"
        class="mobile-drawer"
        :with-header="true"
      >
        <div class="drawer-nav">
          <button class="drawer-link" :class="{ active: isActiveRoute('/list/lost') }" @click="navAndClose(goToLostSquare)">
            <el-icon><Search /></el-icon>
            <span>失物广场</span>
          </button>
          <button class="drawer-link" :class="{ active: isActiveRoute('/list/found') }" @click="navAndClose(goToFoundSquare)">
            <el-icon><Present /></el-icon>
            <span>拾物广场</span>
          </button>
          <button class="drawer-link" :class="{ active: isActiveRoute('/post') }" @click="navAndClose(goToPost)">
            <el-icon><Plus /></el-icon>
            <span>发布信息</span>
          </button>
          <button v-if="isLoggedInComputed" class="drawer-link" :class="{ active: isActiveRoute('/my-items') }" @click="navAndClose(goToMyItems)">
            <el-icon><FolderOpened /></el-icon>
            <span>我的发布</span>
          </button>
          <button v-if="isLoggedInComputed" class="drawer-link" :class="{ active: isActiveRoute('/my-favorites') }" @click="navAndClose(goToMyFavorites)">
            <el-icon><Star /></el-icon>
            <span>我的收藏</span>
          </button>
          <button v-if="isLoggedInComputed" class="drawer-link" :class="{ active: isActiveRoute('/my-reports') }" @click="navAndClose(goToMyReports)">
            <el-icon><Warning /></el-icon>
            <span>我的举报</span>
          </button>
          <button v-if="isLoggedInComputed" class="drawer-link" :class="{ active: isActiveRoute('/my-claims') }" @click="navAndClose(goToMyClaims)">
            <el-icon><Trophy /></el-icon>
            <span>我的认领</span>
          </button>
          <button v-if="isLoggedInComputed" class="drawer-link" :class="{ active: isActiveRoute('/claim-management') }" @click="navAndClose(goToClaimManagement)">
            <el-icon><DocumentChecked /></el-icon>
            <span>认领管理</span>
          </button>
          <button v-if="isLoggedInComputed && user?.role === 'admin'" class="drawer-link" :class="{ active: isActiveRoute('/admin') }" @click="navAndClose(goToDashboard)">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据看板</span>
          </button>
        </div>
      </el-drawer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isLoggedIn, getUser, removeToken } from './utils/auth'
import { Compass, User, Bell, ArrowDown, ChatDotRound, Search, Moon, Sunny, Plus, DataAnalysis, Present, FolderOpened, Warning, Star, Trophy, DocumentChecked, Grid } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from './utils/request'

const router = useRouter()
const route = useRoute()

const user = ref(null)
const unreadCount = ref(0)
const unreadMessageCount = ref(0) // 新增：未读私信数
const darkMode = ref(false)
const drawerVisible = ref(false) // 移动端导航抽屉

// 导航并关闭抽屉（移动端）
const navAndClose = (fn) => {
  if (typeof fn === 'function') fn()
  drawerVisible.value = false
}

// 活动菜单项
const activeMenu = computed(() => {
  return route.path
})

// 登录状态
const isLoggedInComputed = computed(() => {
  return isLoggedIn()
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
    // 先清除 token 和用户信息
    removeToken()
    user.value = null
    ElMessage.success('已退出登录')
    // 使用 window.location.replace 强制跳转并刷新页面，确保导航栏状态立即更新
    // 添加时间戳参数确保 URL 变化，强制触发完整页面刷新
    setTimeout(() => {
      window.location.replace(`/login?t=${Date.now()}`)
    }, 300)
  }
}

// 导航方法
const goHome = () => router.push('/')
const goToLogin = () => router.push('/login')
const goToRegister = () => router.push('/register')
const goToNotifications = () => router.push('/notifications')
const goToMessages = () => router.push('/messages')
const goToLostSquare = () => router.push('/list/lost')
const goToFoundSquare = () => router.push('/list/found')
const goToPost = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/post')
}
const goToMyItems = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/my-items')
}
const goToMyReports = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/my-reports')
}
const goToMyClaims = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/my-claims')
}
const goToClaimManagement = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/claim-management')
}
const goToMyFavorites = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/my-favorites')
}
const goToDashboard = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/admin')
}

// 检查路由是否激活
const isActiveRoute = (path) => {
  return route.path.startsWith(path)
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
  background-color: var(--color-primary);
}

.app-header {
  background: var(--color-card);
  border-bottom: var(--border-width) solid var(--border-color);
  padding: 0;
  padding-top: env(safe-area-inset-top, 0);
  height: 80px;
  min-height: calc(80px + env(safe-area-inset-top, 0));
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 0px 0px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 100%;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  gap: 1rem;
  overflow: hidden;
}

/* 移动端汉堡按钮：默认隐藏，仅小屏显示 */
.mobile-menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-size: 1.25rem;
}

.mobile-menu-btn:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

/* Logo 区域 */
.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.logo-section:hover {
  transform: scale(1.02);
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-accent);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  color: white;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.app-title {
  font-size: 1.4rem;
  font-weight: 900;
  color: var(--color-text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
  letter-spacing: -0.02em;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  justify-content: center;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  min-width: 0;
}

.nav-menu::-webkit-scrollbar {
  display: none;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: var(--border-width) solid transparent;
  border-radius: var(--border-radius);
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-link:hover {
  background: var(--color-primary);
  border-color: var(--border-color);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  transform: translateY(-2px) translateX(-2px);
}

.nav-link.active {
  background: var(--color-accent);
  color: white;
  border-color: var(--border-color);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.nav-link:active {
  transform: translateY(0) translateX(0);
  box-shadow: 2px 2px 0px 0px var(--shadow-color);
}


/* 用户区域 */
.user-section {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-shrink: 0;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-size: 1.2rem;
}

.icon-btn:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.icon-btn:active {
  transform: translateY(0) translateX(0);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--color-text);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-family: inherit;
  font-size: 0.95rem;
}

.user-btn:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.nav-btn {
  padding: 0.6rem 1.2rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--color-text);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-family: inherit;
  font-size: 0.95rem;
}

.nav-btn:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.nav-btn-primary {
  background: var(--color-accent);
  color: white;
}

.message-badge,
.notification-badge {
  display: flex;
  align-items: center;
}

.message-badge :deep(.el-badge__content),
.notification-badge :deep(.el-badge__content) {
  background-color: #f56565;
  border: 2px solid var(--color-card);
  font-weight: 700;
}

.app-main {
  padding: 0;
  min-height: calc(100vh - 80px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .nav-link {
    padding: 0.5rem 0.8rem;
    font-size: 0.85rem;
  }
}

@media (max-width: 1024px) {
  .nav-link {
    padding: 0.4rem 0.7rem;
    font-size: 0.8rem;
  }
  
  .app-title {
    font-size: 1.1rem;
  }
}

@media (max-width: 768px) {
  .app-header {
    height: 64px;
    min-height: calc(64px + env(safe-area-inset-top, 0));
  }
  
  .header-content {
    padding: 0 calc(0.5rem + env(safe-area-inset-right, 0)) 0 calc(0.5rem + env(safe-area-inset-left, 0));
    gap: 0.5rem;
  }
  
  /* 小屏：显示汉堡、隐藏顶部横向导航 */
  .mobile-menu-btn {
    display: flex;
    flex-shrink: 0;
  }
  
  .nav-menu {
    display: none !important;
  }
  
  .app-title {
    font-size: 1rem;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .logo-icon {
    width: 36px;
    height: 36px;
  }
  
  .user-btn span {
    display: none;
  }
  
  .user-btn {
    padding: 0.5rem 0.75rem;
    min-width: 44px;
  }
  
  .icon-btn {
    width: 40px;
    height: 40px;
    min-width: 40px;
    min-height: 40px;
  }
  
  .nav-btn {
    padding: 0.5rem 0.9rem;
    font-size: 0.9rem;
    min-height: 44px;
  }
  
  .app-main {
    min-height: calc(100vh - 64px - env(safe-area-inset-top, 0));
    padding-bottom: env(safe-area-inset-bottom, 0);
  }
}

/* 移动端导航抽屉样式 */
.mobile-drawer :deep(.el-drawer__header) {
  margin-bottom: 0.5rem;
  padding: 1rem 1.25rem;
  border-bottom: var(--border-width) solid var(--border-color);
  font-weight: 700;
  color: var(--color-text);
}

.mobile-drawer :deep(.el-drawer__body) {
  padding: 0.75rem;
  background: var(--color-primary);
}

.drawer-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.drawer-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.875rem 1rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-family: inherit;
  text-align: left;
  min-height: 48px;
}

.drawer-link:hover {
  background: var(--color-primary);
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.drawer-link.active {
  background: var(--color-accent);
  color: white;
  border-color: var(--border-color);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.drawer-link .el-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}
</style>