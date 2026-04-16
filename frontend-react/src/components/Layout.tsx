// 全局布局组件：深色侧边栏 + 白色顶栏 + 内容区。
// 所有需要登录才能访问的页面都渲染在这个布局里。
// 侧边栏导航项根据当前路径自动切换（工单系统 / AI 系统）。

import { useState } from 'react'
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// ── 导航结构定义 ──────────────────────────────────────────────────────────

interface NavChild {
  label: string
  path: string
}

interface NavItem {
  label: string
  icon: string
  path?: string          // 有 path 表示直接跳转
  children?: NavChild[]  // 有 children 表示可展开
}

// 工单系统导航（含 AI 工单助手）
const ticketNavItems: NavItem[] = [
  { label: '首页', icon: '🏠', path: '/' },
  {
    label: '工单管理',
    icon: '📋',
    children: [
      { label: '工单列表', path: '/tickets' },
      { label: '创建工单', path: '/tickets/new' },
    ],
  },
  {
    label: '资产管理',
    icon: '🖥️',
    children: [
      { label: '资产列表', path: '/assets' },
      { label: '创建资产', path: '/assets/new' },
    ],
  },
  {
    label: '运行记录',
    icon: '▶️',
    children: [
      { label: '运行列表', path: '/runs' },
      { label: '创建运行', path: '/runs/new' },
    ],
  },
  { label: 'AI 工单助手', icon: '🤖', path: '/ai/ticket' },
]

// AI 系统导航（算命师 + 量化先知）
const aiNavItems: NavItem[] = [
  { label: '首页', icon: '🏠', path: '/' },
  { label: 'AI 算命师', icon: '🔮', path: '/ai/fortune' },
  { label: 'AI 量化先知', icon: '📈', path: '/ai/stock' },
]

// 只有 /ai/fortune 和 /ai/stock 才显示 AI 系统导航，
// /ai/ticket 归属工单系统（AI 工单助手是工单系统的一部分）
function getNavItems(pathname: string): NavItem[] {
  if (pathname.startsWith('/ai/fortune') || pathname.startsWith('/ai/stock')) {
    return aiNavItems
  }
  return ticketNavItems
}

// ── Layout 组件 ────────────────────────────────────────────────────────────

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  // 侧边栏折叠状态
  const [collapsed, setCollapsed] = useState(false)
  // 记录哪些可展开项是打开的，key 为 label
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const navItems = getNavItems(location.pathname)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function toggleExpand(label: string) {
    setExpanded(prev => ({ ...prev, [label]: !prev[label] }))
  }

  // 判断直接链接是否激活
  function isActive(path: string) {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  // 判断可展开组是否有子项被激活（用于自动展开）
  function isGroupActive(item: NavItem) {
    return item.children?.some(c => location.pathname.startsWith(c.path)) ?? false
  }

  // 展开状态 = 手动打开 或 当前路径在该组下
  function isExpanded(item: NavItem) {
    return expanded[item.label] || isGroupActive(item)
  }

  return (
    <div className="layout">
      {/* 侧边栏 */}
      <aside className={`sidebar${collapsed ? ' sidebar--collapsed' : ''}`}>
        {/* Logo */}
        <div className="sidebar__logo">
          <span className="sidebar__logo-icon">⚡</span>
          {!collapsed && <span className="sidebar__logo-text">Traceable</span>}
        </div>

        {/* 导航 */}
        <nav className="sidebar__nav">
          {navItems.map(item => (
            <div key={item.label}>
              {item.path ? (
                // 直接跳转的导航项
                <Link
                  to={item.path}
                  className={`sidebar__item${isActive(item.path) ? ' sidebar__item--active' : ''}`}
                >
                  <span className="sidebar__item-icon">{item.icon}</span>
                  {!collapsed && <span className="sidebar__item-label">{item.label}</span>}
                </Link>
              ) : (
                // 可展开的导航组
                <>
                  <button
                    className={`sidebar__item sidebar__item--group${isGroupActive(item) ? ' sidebar__item--active' : ''}`}
                    onClick={() => toggleExpand(item.label)}
                  >
                    <span className="sidebar__item-icon">{item.icon}</span>
                    {!collapsed && (
                      <>
                        <span className="sidebar__item-label">{item.label}</span>
                        <span className={`sidebar__chevron${isExpanded(item) ? ' sidebar__chevron--open' : ''}`}>
                          ›
                        </span>
                      </>
                    )}
                  </button>

                  {/* 子菜单，折叠侧边栏时隐藏 */}
                  {!collapsed && isExpanded(item) && (
                    <div className="sidebar__submenu">
                      {item.children?.map(child => (
                        <Link
                          key={child.path}
                          to={child.path}
                          className={`sidebar__subitem${location.pathname === child.path ? ' sidebar__subitem--active' : ''}`}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </nav>
      </aside>

      {/* 右侧主区域 */}
      <div className="layout__main">
        {/* 顶栏 */}
        <header className="header">
          <button
            className="header__hamburger"
            onClick={() => setCollapsed(c => !c)}
            title="折叠/展开侧边栏"
          >
            ☰
          </button>

          <div className="header__right">
            {/* 管理员标识，只有 is_admin 为 true 时显示 */}
            {user?.is_admin && <span className="header__admin-badge">管理员</span>}
            <span className="header__username">{user?.full_name || user?.username}</span>
            <button className="header__logout" onClick={handleLogout}>退出登录</button>
          </div>
        </header>

        {/* 页面内容，由子路由渲染到这里 */}
        {/* Outlet 是 React Router 的约定：嵌套路由的子组件渲染在此处，对应 Vue 的 <RouterView /> */}
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
