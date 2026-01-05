import axios from 'axios'
import { getToken, removeToken } from './auth'
import { ElMessage } from 'element-plus'
import router from '../router'

const API_ORIGIN = import.meta.env.VITE_API_BASE || `http://${location.hostname}:5000`
const request = axios.create({
  baseURL: `${API_ORIGIN}/api`,
  timeout: 10000
})
export const apiOrigin = API_ORIGIN
export const absoluteUrl = (path) => {
  if (!path) return ''
  return path.startsWith('http') ? path : `${API_ORIGIN}${path}`
}
export const previewList = (path) => {
  if (!path) return []
  const u = absoluteUrl(path)
  return u ? [u] : []
}

// 支持多张图片的预览列表
export const previewListMultiple = (urls) => {
  if (!urls || !Array.isArray(urls)) return []
  return urls.map(url => absoluteUrl(url)).filter(url => url)
}

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      // 确保 Authorization header 格式正确
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('响应错误:', error)
    
    if (error.response) {
      const currentPath = router.currentRoute.value.path
      const isAuthRoute = currentPath === '/login' || currentPath === '/register'
      const isAuthRequest = (error.config?.url || '').includes('/auth/')
      const hasToken = !!getToken()

      if (error.response.status === 400) {
        const msg = error.response.data.message || error.response.data.msg
        if (msg === '不能与自己创建会话') {
          return Promise.reject(error)
        }
      }
      switch (error.response.status) {
        case 401:
          if (hasToken && !isAuthRoute && !isAuthRequest) {
            ElMessage.error('登录已过期，请重新登录')
            removeToken()
            router.push('/login')
          }
          break
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          // JWT 验证失败
          if (hasToken && !isAuthRoute && !isAuthRequest) {
            ElMessage.error('身份验证失败，请重新登录')
            removeToken()
            router.push('/login')
          }
          break
        default:
          ElMessage.error(error.response.data.message || error.response.data.msg || '服务器错误')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
