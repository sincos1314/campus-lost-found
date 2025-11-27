import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, getUser } from '../utils/auth'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue')
    },
    {
      path: '/post',
      name: 'post',
      component: () => import('../views/PostItem.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/list/:category',
      name: 'list',
      component: () => import('../views/ItemList.vue')
    },
    {
      path: '/item/:id',
      name: 'detail',
      component: () => import('../views/ItemDetail.vue')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/user/:id/items',
      name: 'userItems',
      component: () => import('../views/UserItems.vue')
    },
    {
      path: '/my-items',
      name: 'myItems',
      component: () => import('../views/MyItems.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('../views/NotificationsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/my-reports',
      name: 'myReports',
      component: () => import('../views/MyReports.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/messages',
      name: 'messages',
      component: () => import('../views/MessagesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/chat/:id',
      name: 'chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true }
    }
    ,{
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminView.vue')
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !isLoggedIn()) {
    ElMessage.warning('请先登录')
    next('/login')
  } else if (to.path === '/admin') {
    if (!isLoggedIn()) {
      ElMessage.warning('请先登录')
      next('/login')
    } else {
      const u = getUser()
      if (u?.role !== 'admin') {
        ElMessage.error('无权限访问后台')
        next('/')
      } else {
        next()
      }
    }
  } else if (isLoggedIn() && getUser()?.is_banned) {
    const blocked = ['/post']
    if (blocked.includes(to.path)) {
      ElMessage.error('账户已被封禁，暂不可使用该功能')
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
