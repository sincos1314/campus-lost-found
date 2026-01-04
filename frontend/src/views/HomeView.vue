<template>
  <div class="home-container">
    <!-- 装饰性 Blob 元素 -->
    <div class="blob blob-orange"></div>
    <div class="blob blob-green"></div>

    <!-- Hero 区域 -->
    <div class="hero-section">
      <!-- 标签 -->
      <div class="hero-badge">
        🚀 校园生活更便利
      </div>

      <!-- 主标题 - 闪卡效果 -->
      <h1 
        class="hero-title holographic-text"
        ref="titleRef"
        @mousemove="handleMouseMove"
        @mouseleave="handleMouseLeave"
      >
        哎呀，东西丢了吗？
      </h1>

      <!-- 副标题 -->
      <p class="hero-subtitle">
        UniFind 帮你快速找回遗失的宝贝，或者帮助迷路的物品回到主人身边。简单、安全、有爱！
      </p>

      <!-- 行动按钮组 -->
      <div class="hero-actions">
        <button 
          class="action-btn action-btn-white"
          @click="goToSquare"
        >
          🔍 去广场看看
        </button>
        <button 
          class="action-btn action-btn-blue"
          @click="goToPost"
        >
          ➕ 我要发布 →
        </button>
      </div>
    </div>

    <!-- 统计看板 -->
    <div class="stats-section">
      <div class="stats-container">
        <div 
          v-for="(stat, index) in stats"
          :key="stat.key"
          class="stat-card"
          :class="`stat-card-${stat.key}`"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="stat-icon-wrapper">
            <div class="stat-icon" :class="`icon-${stat.key}`">
              {{ stat.icon }}
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value" :data-target="stat.value">
              {{ animatedValues[stat.key] }}
            </div>
          </div>
          <div class="stat-decoration"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn } from '../utils/auth'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const titleRef = ref(null)

const stats = ref([
  { key: 'users', label: '注册用户数', icon: '👥', value: 0, color: '#3B82F6' },
  { key: 'lost', label: '失物数量', icon: '🔍', value: 0, color: '#F59E0B' },
  { key: 'found', label: '拾物数量', icon: '🎁', value: 0, color: '#10B981' },
  { key: 'solved', label: '已寻回数量', icon: '✅', value: 0, color: '#EF4444' }
])

const animatedValues = ref({
  users: 0,
  lost: 0,
  found: 0,
  solved: 0
})

// 数字滚动动画
const animateNumber = (key, target, duration = 2000) => {
  const start = 0
  const increment = target / (duration / 16) // 60fps
  let current = start
  
  const timer = setInterval(() => {
    current += increment
    if (current >= target) {
      current = target
      clearInterval(timer)
    }
    animatedValues.value[key] = Math.floor(current)
  }, 16)
}

// 加载统计数据
const loadStats = async () => {
  try {
    const data = await request.get('/stats')
    // 更新统计数据
    if (data) {
      stats.value[0].value = data.total_users || 0
      stats.value[1].value = data.total_lost || 0
      stats.value[2].value = data.total_found || 0
      stats.value[3].value = data.total_solved || 0
      
      // 延迟启动动画，让卡片先出现
      setTimeout(() => {
        stats.value.forEach(stat => {
          if (stat.value > 0) {
            animateNumber(stat.key, stat.value)
          }
        })
      }, 300)
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    // 即使失败也显示0，避免页面空白
    stats.value.forEach(stat => {
      stat.value = 0
      animatedValues.value[stat.key] = 0
    })
  }
}

const goToSquare = () => {
  router.push('/list/lost')
}

const goToPost = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  router.push('/post')
}

// 闪卡效果：处理鼠标移动
const handleMouseMove = (e) => {
  if (!titleRef.value) return
  
  const rect = titleRef.value.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  
  // 计算鼠标相对于元素中心的位置（-1 到 1）
  const x = (e.clientX - centerX) / (rect.width / 2)
  const y = (e.clientY - centerY) / (rect.height / 2)
  
  // 计算倾斜角度（最大15度）
  const rotateX = y * 15
  const rotateY = -x * 15
  
  // 计算渐变角度（0-360度）
  const gradientAngle = Math.atan2(y, x) * (180 / Math.PI) + 180
  
  // 应用3D变换
  titleRef.value.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1)`
  
  // 更新渐变角度
  titleRef.value.style.setProperty('--gradient-angle', `${gradientAngle}deg`)
}

// 鼠标离开时恢复
const handleMouseLeave = () => {
  if (!titleRef.value) return
  titleRef.value.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)'
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.home-container {
  position: relative;
  min-height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  overflow-x: hidden;
}

/* 装饰性 Blob 元素 */
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.6;
  pointer-events: none;
  z-index: 0;
}

.blob-orange {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255, 100, 50, 0.4) 0%, rgba(255, 150, 100, 0.2) 100%);
  top: 10%;
  left: 5%;
  animation: float 8s ease-in-out infinite;
}

.blob-green {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(50, 200, 100, 0.4) 0%, rgba(100, 250, 150, 0.2) 100%);
  bottom: 10%;
  right: 5%;
  animation: float 10s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(30px, -30px) scale(1.1);
  }
}

/* Hero 区域 */
.hero-section {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

/* 标签 */
.hero-badge {
  display: inline-block;
  background: var(--color-card);
  color: var(--color-text);
  border: var(--border-width) solid var(--border-color);
  border-radius: 50px;
  padding: 0.5rem 1.2rem;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  transform: rotate(-2deg);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hero-badge:hover {
  transform: rotate(-1deg) translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

/* 主标题 */
.hero-title {
  font-size: 4.5rem;
  font-weight: 900;
  line-height: 1.1;
  margin: 0 0 1.5rem 0;
  letter-spacing: -0.02em;
  position: relative;
  display: inline-block;
  cursor: pointer;
  transition: transform 0.1s ease-out;
  transform-style: preserve-3d;
}

/* 闪卡全息效果 */
.holographic-text {
  /* 全息彩虹渐变背景 */
  background: linear-gradient(
    var(--gradient-angle, 135deg),
    #ff006e 0%,
    #8338ec 15%,
    #3a86ff 30%,
    #06ffa5 45%,
    #ffbe0b 60%,
    #fb5607 75%,
    #ff006e 90%,
    #8338ec 100%
  );
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  /* 基础文字颜色作为后备（当渐变不支持时） */
  color: var(--color-text);
  
  /* 多层阴影增强立体感和清晰度 */
  text-shadow: 
    /* 主阴影 - 根据主题调整 */
    0 0 0 var(--color-text),
    0 0 0 var(--color-text),
    /* 外发光效果 - 彩色光晕 */
    0 0 20px rgba(255, 0, 110, 0.3),
    0 0 40px rgba(131, 56, 236, 0.3),
    0 0 60px rgba(58, 134, 255, 0.2),
    /* 硬阴影 - 新野兽派风格 */
    4px 4px 0px rgba(0, 0, 0, 0.15);
  
  /* 确保文字清晰渲染 */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  
  /* 添加轻微的光泽效果 */
  filter: brightness(1.1) contrast(1.05);
}

/* 暗色主题下的闪卡效果 */
body.dark .holographic-text {
  /* 暗色主题下使用更亮的渐变 */
  background: linear-gradient(
    var(--gradient-angle, 135deg),
    #ff006e 0%,
    #8338ec 15%,
    #3a86ff 30%,
    #06ffa5 45%,
    #ffbe0b 60%,
    #fb5607 75%,
    #ff006e 90%,
    #8338ec 100%
  );
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  /* 更亮的阴影效果 */
  text-shadow: 
    0 0 0 var(--color-text),
    0 0 0 var(--color-text),
    0 0 25px rgba(255, 0, 110, 0.5),
    0 0 50px rgba(131, 56, 236, 0.4),
    0 0 75px rgba(58, 134, 255, 0.3),
    4px 4px 0px rgba(255, 255, 255, 0.1);
  
  filter: brightness(1.2) contrast(1.1);
}

/* 亮色主题下的闪卡效果 */
body:not(.dark) .holographic-text {
  /* 亮色主题下使用更饱和的渐变 */
  background: linear-gradient(
    var(--gradient-angle, 135deg),
    #ff006e 0%,
    #8338ec 15%,
    #3a86ff 30%,
    #06ffa5 45%,
    #ffbe0b 60%,
    #fb5607 75%,
    #ff006e 90%,
    #8338ec 100%
  );
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  /* 柔和的阴影效果 */
  text-shadow: 
    0 0 0 var(--color-text),
    0 0 0 var(--color-text),
    0 0 20px rgba(255, 0, 110, 0.25),
    0 0 40px rgba(131, 56, 236, 0.2),
    0 0 60px rgba(58, 134, 255, 0.15),
    4px 4px 0px rgba(0, 0, 0, 0.2);
  
  filter: brightness(1.05) contrast(1.02);
}

/* 副标题 */
.hero-subtitle {
  font-size: 1.2rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 3rem 0;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

/* 行动按钮组 */
.hero-actions {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.action-btn {
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
  font-weight: 700;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-family: inherit;
}

.action-btn-white {
  background: var(--color-card);
  color: var(--color-text);
}

.action-btn-blue {
  background: var(--color-accent);
  color: white;
  border-color: var(--border-color);
}

/* Hover 效果：阴影位置移动，产生按压感 */
.action-btn:hover {
  transform: translateY(2px) translateX(2px);
  box-shadow: 2px 2px 0px 0px var(--shadow-color);
}

.action-btn:active {
  transform: translateY(4px) translateX(4px);
  box-shadow: 0px 0px 0px 0px var(--shadow-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-title {
    font-size: 3rem;
  }

  .hero-subtitle {
    font-size: 1rem;
    padding: 0 1rem;
  }

  .hero-actions {
    flex-direction: column;
    align-items: center;
  }

  .action-btn {
    width: 100%;
    max-width: 300px;
  }

  .blob-orange,
  .blob-green {
    width: 250px;
    height: 250px;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 2.5rem;
  }

  .hero-badge {
    font-size: 0.8rem;
    padding: 0.4rem 1rem;
  }
}

/* 统计看板区域 */
.stats-section {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1200px;
  margin: 4rem auto 2rem;
  padding: 0 2rem;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  animation: fadeInUp 0.6s ease-out;
}

/* 统计卡片 */
.stat-card {
  position: relative;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 2rem;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
  animation: slideInUp 0.6s ease-out both;
  cursor: default;
}

.stat-card:hover {
  transform: translateY(-4px) translateX(-4px);
  box-shadow: calc(var(--shadow-offset) + 4px) calc(var(--shadow-offset) + 4px) 0px 0px var(--shadow-color);
}

/* 图标区域 */
.stat-icon-wrapper {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 100px;
  height: 100px;
  opacity: 0.15;
  transform: rotate(15deg);
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon-wrapper {
  transform: rotate(25deg) scale(1.1);
}

.stat-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  filter: blur(2px);
}

/* 内容区域 */
.stat-content {
  position: relative;
  z-index: 2;
}

.stat-label {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 3rem;
  font-weight: 900;
  color: var(--color-text);
  line-height: 1;
  font-family: 'Arial Black', sans-serif;
  position: relative;
}

.stat-value::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 60px;
  height: 4px;
  background: var(--color-accent);
  border-radius: 2px;
}

/* 装饰元素 */
.stat-decoration {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 6px;
  background: linear-gradient(90deg, 
    var(--color-accent) 0%, 
    transparent 100%);
  opacity: 0.6;
}

/* 不同卡片的特殊样式 */
.stat-card-users {
  border-left: 6px solid #3B82F6;
}

.stat-card-users .stat-value::after {
  background: #3B82F6;
}

.stat-card-lost {
  border-left: 6px solid #F59E0B;
}

.stat-card-lost .stat-value::after {
  background: #F59E0B;
}

.stat-card-found {
  border-left: 6px solid #10B981;
}

.stat-card-found .stat-value::after {
  background: #10B981;
}

.stat-card-solved {
  border-left: 6px solid #EF4444;
}

.stat-card-solved .stat-value::after {
  background: #EF4444;
}

/* 动画 */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats-section {
    margin-top: 3rem;
    padding: 0 1rem;
  }

  .stats-container {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .stat-card {
    padding: 1.5rem;
  }

  .stat-value {
    font-size: 2.5rem;
  }

  .stat-icon-wrapper {
    width: 80px;
    height: 80px;
    top: -15px;
    right: -15px;
  }

  .stat-icon {
    font-size: 3rem;
  }
}

@media (max-width: 480px) {
  .stats-section {
    margin-top: 2rem;
  }

  .stat-card {
    padding: 1.2rem;
  }

  .stat-value {
    font-size: 2rem;
  }

  .stat-label {
    font-size: 0.85rem;
  }
}
</style>