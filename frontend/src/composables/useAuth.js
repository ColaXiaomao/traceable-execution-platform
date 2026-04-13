/**
 * useAuth —— 全局认证状态
 * 用 Vue 的响应式系统管理 token 和当前用户
 * 模块级单例：整个应用共享同一份状态
 */

import { ref, computed } from 'vue'
import { authApi } from '@/api/index.js'

const token = ref(localStorage.getItem('access_token'))
// 这里从浏览器 localStorage 读取 token。
const user = ref(null)

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    const data = await authApi.login(username, password)
    token.value = data.access_token
    localStorage.setItem('access_token', data.access_token)
    // 登录成功后拉取当前用户信息
    user.value = await authApi.me()
  }

  async function register(username, email, password, fullName) {
    await authApi.register(username, email, password, fullName)
    // 注册成功后自动登录
    await login(username, password)
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { token, user, isLoggedIn, login, logout, register }
}
