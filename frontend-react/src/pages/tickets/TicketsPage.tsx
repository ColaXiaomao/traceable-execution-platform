// 工单列表页。
// 展示当前用户的所有工单，支持查看详情和创建新工单（跳转到详情页）。

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ticketsApi } from '../../api'
import type { Ticket, TicketStatus } from '../../types'

// 状态对应的中文显示和 badge 样式
const STATUS_LABEL: Record<TicketStatus, string> = {
  draft: '草稿',
  submitted: '待审批',
  approved: '已审批',
  running: '执行中',
  done: '已完成',
  failed: '失败',
  closed: '已关闭',
}

export default function TicketsPage() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // 组件挂载时拉取工单列表，对应 Vue 的 onMounted
  useEffect(() => {
    ticketsApi.list()
      .then(data => setTickets(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, []) // 空依赖 = 只执行一次

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString('zh-CN')
  }

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">工单列表</h2>
        <button
          className="btn btn--primary"
          onClick={() => navigate('/tickets/new')}
        >
          + 创建工单
        </button>
      </div>

      <div className="card">
        {loading && <div className="loading">加载中...</div>}
        {error && <div className="card__body form-error">{error}</div>}

        {!loading && !error && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>标题</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="empty">暂无工单</td>
                  </tr>
                ) : (
                  tickets.map(ticket => (
                    <tr key={ticket.id}>
                      <td>#{ticket.id}</td>
                      <td>{ticket.title}</td>
                      <td>
                        <span className={`badge badge--${ticket.status}`}>
                          {STATUS_LABEL[ticket.status]}
                        </span>
                      </td>
                      <td>{formatDate(ticket.created_at)}</td>
                      <td>
                        <span
                          className="link"
                          onClick={() => navigate(`/tickets/${ticket.id}`)}
                        >
                          查看详情
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
