<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'

const router = useRouter()
const { register } = useAuth()

const username = ref('')
const email = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function handleRegister() {
  if (!username.value || !email.value || !password.value) {
    errorMsg.value = '请填写用户名、邮箱和密码'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    await register(username.value, email.value, password.value, fullName.value)
    router.push('/')
  } catch (e) {
    errorMsg.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-card">
      <h1 class="title">Traceable Execution Platform</h1>
      <p class="subtitle">创建账号以开始使用</p>

      <form @submit.prevent="handleRegister" class="form">
        <div class="field">
          <label for="username">用户名 <span class="required">*</span></label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="输入用户名"
            autocomplete="username"
            :disabled="loading"
          />
        </div>

        <div class="field">
          <label for="email">邮箱 <span class="required">*</span></label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="输入邮箱地址"
            autocomplete="email"
            :disabled="loading"
          />
        </div>

        <div class="field">
          <label for="fullName">姓名（可选）</label>
          <input
            id="fullName"
            v-model="fullName"
            type="text"
            placeholder="输入真实姓名"
            autocomplete="name"
            :disabled="loading"
          />
        </div>

        <div class="field">
          <label for="password">密码 <span class="required">*</span></label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="输入密码"
            autocomplete="new-password"
            :disabled="loading"
          />
        </div>

        <div class="field">
          <label for="confirmPassword">确认密码 <span class="required">*</span></label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
            :disabled="loading"
          />
        </div>

        <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

        <button type="submit" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <p class="switch-link">
        已有账号？
        <router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f6f9;
}

.register-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
  padding: 48px 40px;
  width: 100%;
  max-width: 400px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 6px;
}

.subtitle {
  font-size: 14px;
  color: #888;
  margin: 0 0 32px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 500;
  color: #444;
}

.required {
  color: #e53935;
}

.field input {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.field input:focus {
  border-color: #4f6ef7;
}

.field input:disabled {
  background: #f9f9f9;
  cursor: not-allowed;
}

.error {
  font-size: 13px;
  color: #e53935;
  margin: 0;
}

button[type='submit'] {
  padding: 11px;
  background: #4f6ef7;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

button[type='submit']:hover:not(:disabled) {
  background: #3a58e0;
}

button[type='submit']:disabled {
  background: #a0b0f5;
  cursor: not-allowed;
}

.switch-link {
  margin: 24px 0 0;
  text-align: center;
  font-size: 13px;
  color: #888;
}

.switch-link a {
  color: #4f6ef7;
  text-decoration: none;
  font-weight: 500;
}

.switch-link a:hover {
  text-decoration: underline;
}
</style>
