<template>
  <div class="home-container">
    <el-row :gutter="20">
      <!-- 欢迎横幅 -->
      <el-col :span="24">
        <el-card class="hero-card" shadow="never">
          <div class="hero-content">
            <div class="hero-text">
              <h1>🎓 欢迎使用校园失物招领系统</h1>
              <p>让每一件失物都能找到归宿，传递校园温暖</p>
            </div>
            <el-button
              v-if="!isLoggedIn()"
              type="primary"
              size="large"
              @click="$router.push('/login')"
            >
              立即开始
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 统计卡片 -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card lost-card" shadow="hover">
          <el-statistic title="失物信息" :value="stats.total_lost">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card found-card" shadow="hover">
          <el-statistic title="拾物信息" :value="stats.total_found">
            <template #prefix>
              <el-icon><Present /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card solved-card" shadow="hover">
          <el-statistic title="已找回" :value="stats.total_solved">
            <template #prefix>
              <el-icon><SuccessFilled /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card users-card" shadow="hover">
          <el-statistic title="注册用户" :value="stats.total_users">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>

      <!-- 个人统计（登录后显示） -->
      <el-col :span="24" v-if="isLoggedIn()">
        <el-card class="my-stats-card" shadow="never">
          <template #header>
            <span>我的数据</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="my-stat-item">
                <div class="stat-value">{{ myStats.my_items }}</div>
                <div class="stat-label">发布总数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="my-stat-item">
                <div class="stat-value">{{ myStats.my_lost }}</div>
                <div class="stat-label">失物发布</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="my-stat-item">
                <div class="stat-value">{{ myStats.my_found }}</div>
                <div class="stat-label">拾物发布</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="my-stat-item">
                <div class="stat-value">{{ myStats.my_solved }}</div>
                <div class="stat-label">已解决</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 快速操作 -->
      <el-col :span="24">
        <el-card class="actions-card" shadow="never">
          <template #header>
            <span>快速操作</span>
          </template>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="6">
              <div class="action-item" @click="handleAction('/post', 'lost')">
                <el-icon :size="40" color="#f56565"><Warning /></el-icon>
                <h3>发布失物</h3>
                <p>我丢了东西</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <div class="action-item" @click="handleAction('/post', 'found')">
                <el-icon :size="40" color="#48bb78"><Present /></el-icon>
                <h3>发布拾物</h3>
                <p>我捡到东西</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <div class="action-item" @click="$router.push('/list/lost')">
                <el-icon :size="40" color="#667eea"><Search /></el-icon>
                <h3>查看失物</h3>
                <p>浏览失物信息</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <div class="action-item" @click="$router.push('/list/found')">
                <el-icon :size="40" color="#4299e1"><View /></el-icon>
                <h3>查看拾物</h3>
                <p>浏览拾物信息</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import { isLoggedIn } from '../utils/auth'

const router = useRouter()

const stats = ref({
  total_lost: 0,
  total_found: 0,
  total_solved: 0,
  total_users: 0
})

const myStats = ref({
  my_items: 0,
  my_lost: 0,
  my_found: 0,
  my_solved: 0
})

const loadStats = async () => {
  try {
    const data = await request.get('/stats')
    stats.value = data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadMyStats = async () => {
  if (!isLoggedIn()) return
  try {
    const data = await request.get('/my-stats')
    myStats.value = data
  } catch (error) {
    console.error('加载个人统计失败:', error)
  }
}

const handleAction = (path, category) => {
  if (!isLoggedIn() && path === '/post') {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push({ path, query: { category } })
}

onMounted(() => {
  loadStats()
  loadMyStats()
})
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
}

.hero-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.hero-card :deep(.el-card__body) {
  padding: 60px 40px;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.hero-text h1 {
  font-size: 36px;
  margin-bottom: 15px;
}

.hero-text p {
  font-size: 18px;
  opacity: 0.95;
}

.stat-card {
  margin-bottom: 20px;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.lost-card {
  border-left: 4px solid #f56565;
}

.found-card {
  border-left: 4px solid #48bb78;
}

.solved-card {
  border-left: 4px solid #4299e1;
}

.users-card {
  border-left: 4px solid #9f7aea;
}

.my-stats-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.my-stats-card :deep(.el-card__header) {
  color: white;
  border-bottom-color: rgba(255, 255, 255, 0.3);
}

.my-stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.actions-card {
  margin-bottom: 20px;
}

.action-item {
  text-align: center;
  padding: 30px;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.3s;
  background: #f9fafb;
}

.action-item:hover {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-3px);
}

.action-item h3 {
  margin: 15px 0 8px;
  color: #333;
}

.action-item p {
  color: #666;
  font-size: 14px;
}
</style>
