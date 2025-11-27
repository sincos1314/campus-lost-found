// 存储token
export function setToken(token) {
  localStorage.setItem('access_token', token)
}

// 获取token
export function getToken() {
  return localStorage.getItem('access_token')
}

// 删除token
export function removeToken() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

// 存储用户信息
export function setUser(user) {
  localStorage.setItem('user', JSON.stringify(user))
}

// 获取用户信息
export function getUser() {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
}

// 检查是否登录
export function isLoggedIn() {
  return !!getToken()
}
