// 应用路由总装。
// 用 createBrowserRouter 定义全部路由，ProtectedRoute 保护需要登录的页面，
// Layout 作为父路由将所有子页面渲染进侧边栏布局。

import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'

import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

// 认证页
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

// 首页
import HomePage from './pages/HomePage'

// 工单系统
import TicketsPage from './pages/tickets/TicketsPage'
import TicketDetailPage from './pages/tickets/TicketDetailPage'
import AssetsPage from './pages/assets/AssetsPage'
import AssetDetailPage from './pages/assets/AssetDetailPage'
import RunsPage from './pages/runs/RunsPage'
import RunDetailPage from './pages/runs/RunDetailPage'

// AI 系统
import AiFortunePage from './pages/ai/AiFortunePage'
import AiStockPage from './pages/ai/AiStockPage'
import AiTicketPage from './pages/ai/AiTicketPage'

// React Router v6 的 createBrowserRouter 写法比 <BrowserRouter> 更推荐，
// 支持 loader/action 数据预取（虽然本项目暂时用不上）。
const router = createBrowserRouter([
  // ── 公开页面（无需登录）─────────────────────────────────────────────────
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },

  // ── 需要登录的页面（ProtectedRoute 做守卫，Layout 提供侧边栏布局）─────
  {
    element: (
      // ProtectedRoute 检查是否已登录，未登录则重定向到 /login
      <ProtectedRoute>
        {/* Layout 包含侧边栏+顶栏，子路由内容通过 <Outlet /> 注入 */}
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      // 首页
      { path: '/', element: <HomePage /> },

      // 工单系统
      { path: '/tickets', element: <TicketsPage /> },
      { path: '/tickets/:id', element: <TicketDetailPage /> },  // :id = 'new' 或数字

      // 资产管理
      { path: '/assets', element: <AssetsPage /> },
      { path: '/assets/:id', element: <AssetDetailPage /> },

      // 运行记录
      { path: '/runs', element: <RunsPage /> },
      { path: '/runs/:id', element: <RunDetailPage /> },

      // AI 工单助手（归属工单系统侧边栏）
      { path: '/ai/ticket', element: <AiTicketPage /> },

      // AI 系统（独立侧边栏，见 Layout.tsx getNavItems）
      { path: '/ai/fortune', element: <AiFortunePage /> },
      { path: '/ai/stock', element: <AiStockPage /> },

      // /ai 直接重定向到算命师
      { path: '/ai', element: <Navigate to="/ai/fortune" replace /> },

      // 未匹配路径回到首页
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

// App 是整个应用的根，AuthProvider 放在最外层，所有子组件都能用 useAuth()
export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  )
}
