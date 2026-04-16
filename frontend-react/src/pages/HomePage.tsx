// 系统选择页，登录后的第一个页面。
// 展示两张入口卡片，分别进入工单系统和 AI 助手系统。

import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function HomePage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  return (
    <div className="home-page">
      <div className="home-page__greeting">
        欢迎回来，{user?.full_name || user?.username}
      </div>
      <p className="home-page__subtitle">请选择要进入的系统</p>

      <div className="home-page__grid">
        <div className="system-card" onClick={() => navigate('/tickets')}>
          <div className="system-card__icon">📋</div>
          <div className="system-card__info">
            <span className="system-card__title">工单系统</span>
            <span className="system-card__desc">工单管理 · 资产管理 · 执行记录</span>
          </div>
        </div>

        <div className="system-card" onClick={() => navigate('/ai')}>
          <div className="system-card__icon">🤖</div>
          <div className="system-card__info">
            <span className="system-card__title">AI 助手</span>
            <span className="system-card__desc">AI 算命师 · AI 量化先知</span>
          </div>
        </div>
      </div>
    </div>
  )
}
