<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'

const router = useRouter()
const { user, logout } = useAuth()

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="home">
    <header class="header">
      <span class="brand">Traceable Execution Platform</span>
      <div class="user-bar">
        <span v-if="user" class="username">{{ user.username }}</span>
        <button @click="handleLogout" class="logout-btn">退出登录</button>
      </div>
    </header>
    <main class="content">
      <p>欢迎，已登录</p>
    </main>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  background: #f4f6f9;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 56px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.brand {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.user-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  font-size: 14px;
  color: #555;
}

.logout-btn {
  padding: 6px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: #444;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #f5f5f5;
}

.content {
  padding: 40px 32px;
  font-size: 15px;
  color: #666;
}
</style>
