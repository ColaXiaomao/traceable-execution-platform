// 登录页面。
// 对应 Vue 版本的 LoginView.vue，逻辑完全一致，
// v-model 换成 useState + onChange，@submit.prevent 换成 onSubmit + e.preventDefault()。

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    // 阻止表单默认的页面刷新行为，对应 Vue 的 @submit.prevent
    e.preventDefault()

    if (!username || !password) {
      setErrorMsg('请输入用户名和密码')
      return
    }

    setLoading(true)
    setErrorMsg('')

    try {
      await login(username, password)
      navigate('/')
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Traceable Execution Platform</h1>
        <p className="auth-subtitle">请登录以继续</p>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-field">
            <label htmlFor="username">用户名</label>
            {/* React 用 value + onChange 实现双向绑定，对应 Vue 的 v-model */}
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="输入用户名"
              autoComplete="username"
              disabled={loading}
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">密码</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="输入密码"
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          {errorMsg && <p className="form-error">{errorMsg}</p>}

          <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <p className="auth-switch">
          没有账号？<Link to="/register">去注册</Link>
        </p>
      </div>
    </div>
  )
}
