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
      <div class="card-grid">
        <a href="/api/v1/agent/fortune/demo" class="app-card">
          <div class="card-icon">🔮</div>
          <div class="card-info">
            <span class="card-title">AI 算命师</span>
            <span class="card-desc">基于 AI 的命理分析与运势预测</span>
          </div>
        </a>
        <a href="/api/v1/agent1/stock/demo" class="app-card">
          <div class="card-icon">📈</div>
          <div class="card-info">
            <span class="card-title">AI 量化先知</span>
            <span class="card-desc">实时 A 股行情 · 短期走势预测</span>
          </div>
        </a>
      </div>
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
}

.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.app-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  width: 560px;
  padding: 48px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, transform 0.2s;
}

.app-card:hover {
  box-shadow: 0 6px 24px rgba(79, 110, 247, 0.15);
  transform: translateY(-2px);
}

.card-icon {
  font-size: 72px;
  line-height: 1;
}

.card-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.card-title {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a1a;
}

.card-desc {
  font-size: 14px;
  color: #888;
}
</style>
