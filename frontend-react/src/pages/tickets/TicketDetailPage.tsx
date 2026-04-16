// 工单详情页，同时兼任创建页（路由 /tickets/new）。
// 包含：工单信息、附件上传/列表、执行记录、LLM 分析触发、管理员审批。

import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ticketsApi, artifactsApi, runsApi, workflowsApi } from '../../api'
import { useAuth } from '../../context/AuthContext'
import type { Ticket, Artifact, Run, TicketStatus, TicketCreate } from '../../types'

const STATUS_LABEL: Record<TicketStatus, string> = {
  draft: '草稿', submitted: '待审批', approved: '已审批',
  running: '执行中', done: '已完成', failed: '失败', closed: '已关闭',
}

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  // id === 'new' 时为创建模式，否则为详情模式
  const isNew = id === 'new'

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(!isNew)
  const [error, setError] = useState('')

  // 创建表单状态
  const [form, setForm] = useState<TicketCreate>({ title: '', description: '' })
  const [submitting, setSubmitting] = useState(false)

  // 附件上传
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)

  // LLM 分析
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<string | null>(null)

  // 加载工单详情及其关联数据
  useEffect(() => {
    if (isNew) return

    const ticketId = Number(id)
    setLoading(true)

    // 并行请求工单信息、附件列表、执行记录，减少等待时间
    Promise.all([
      ticketsApi.get(ticketId),
      artifactsApi.listByTicket(ticketId),
      runsApi.list(ticketId),
    ])
      .then(([t, a, r]) => {
        setTicket(t)
        setArtifacts(a)
        setRuns(r)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id, isNew])

  // 创建新工单
  async function handleCreate() {
    if (!form.title.trim()) return
    setSubmitting(true)
    try {
      const created = await ticketsApi.create(form)
      navigate(`/tickets/${created.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 上传附件
  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !ticket) return

    setUploading(true)
    try {
      const res = await artifactsApi.upload(ticket.id, file)
      // 上传成功后把新附件追加到列表，不需要重新拉整个列表
      setArtifacts(prev => [...prev, res.artifact])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
      // 清空 input，允许重复上传同名文件
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  // 触发 LLM 分析（使用第一个附件）
  async function handleAnalyze() {
    if (!ticket || artifacts.length === 0) return
    setAnalyzing(true)
    setAnalysisResult(null)
    try {
      const res = await workflowsApi.analyzeRouterConfig(ticket.id, artifacts[0].id)
      setAnalysisResult(res.analysis || res.error || '分析完成')
    } catch (err: unknown) {
      setAnalysisResult(err instanceof Error ? err.message : '分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  // 审批工单（仅管理员）
  async function handleApprove() {
    if (!ticket) return
    try {
      const updated = await ticketsApi.approve(ticket.id)
      setTicket(updated)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '审批失败')
    }
  }

  // 创建执行记录
  async function handleCreateRun(runType: 'proof' | 'action') {
    if (!ticket) return
    try {
      const run = await runsApi.create(ticket.id, runType)
      setRuns(prev => [run, ...prev])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '创建失败')
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString('zh-CN')
  }

  // ── 创建模式 ────────────────────────────────────────────────────────────

  if (isNew) {
    return (
      <div>
        <div className="page-header">
          <h2 className="page-title">创建工单</h2>
        </div>

        <div className="card">
          <div className="card__body">
            <div className="form">
              <div className="form-field">
                <label>标题 <span className="required">*</span></label>
                <input
                  type="text"
                  value={form.title}
                  onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                  placeholder="输入工单标题"
                />
              </div>

              <div className="form-field">
                <label>描述</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="输入工单描述（可选）"
                />
              </div>

              {error && <p className="form-error">{error}</p>}

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  className="btn btn--primary"
                  onClick={handleCreate}
                  disabled={submitting || !form.title.trim()}
                >
                  {submitting ? '提交中...' : '创建工单'}
                </button>
                <button
                  className="btn btn--secondary"
                  onClick={() => navigate('/tickets')}
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── 详情模式 ────────────────────────────────────────────────────────────

  if (loading) return <div className="loading">加载中...</div>
  if (error && !ticket) return <div className="form-error">{error}</div>
  if (!ticket) return null

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h2 className="page-title">工单 #{ticket.id}</h2>
          <span className={`badge badge--${ticket.status}`}>
            {STATUS_LABEL[ticket.status]}
          </span>
        </div>
        <button className="btn btn--secondary" onClick={() => navigate('/tickets')}>
          返回列表
        </button>
      </div>

      {error && <p className="form-error" style={{ marginBottom: 12 }}>{error}</p>}

      {/* 工单基本信息 */}
      <div className="card">
        <div className="card__header">
          <span className="card__title">基本信息</span>
          {/* 管理员且状态为 submitted 时显示审批按钮 */}
          {user?.is_admin && ticket.status === 'submitted' && (
            <button className="btn btn--success btn--sm" onClick={handleApprove}>
              审批通过
            </button>
          )}
        </div>
        <div className="card__body">
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">标题</span>
              <span>{ticket.title}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">描述</span>
              <span>{ticket.description || '—'}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">创建时间</span>
              <span>{formatDate(ticket.created_at)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">更新时间</span>
              <span>{formatDate(ticket.updated_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 附件 */}
      <div className="card">
        <div className="card__header">
          <span className="card__title">附件</span>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* 触发 LLM 分析，需要至少一个附件 */}
            {artifacts.length > 0 && (
              <button
                className="btn btn--secondary btn--sm"
                onClick={handleAnalyze}
                disabled={analyzing}
              >
                {analyzing ? '分析中...' : 'LLM 分析'}
              </button>
            )}
            <button
              className="btn btn--primary btn--sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? '上传中...' : '上传附件'}
            </button>
            {/* 隐藏的 file input，由按钮触发 */}
            <input
              ref={fileInputRef}
              type="file"
              style={{ display: 'none' }}
              onChange={handleUpload}
            />
          </div>
        </div>
        <div className="card__body">
          {analysisResult && (
            <div className="analysis-result">{analysisResult}</div>
          )}
          {artifacts.length === 0 ? (
            <div className="empty">暂无附件</div>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>文件名</th>
                    <th>类型</th>
                    <th>大小</th>
                    <th>上传时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {artifacts.map(a => (
                    <tr key={a.id}>
                      <td>{a.filename}</td>
                      <td>{a.artifact_type || '—'}</td>
                      <td>{(a.size_bytes / 1024).toFixed(1)} KB</td>
                      <td>{formatDate(a.created_at)}</td>
                      <td>
                        <a
                          className="link"
                          href={artifactsApi.downloadUrl(a.id)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          下载
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* 执行记录 */}
      <div className="card">
        <div className="card__header">
          <span className="card__title">执行记录</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn btn--secondary btn--sm"
              onClick={() => handleCreateRun('proof')}
            >
              + Proof Run
            </button>
            {/* ActionRun 需要工单已审批 */}
            {ticket.status === 'approved' && (
              <button
                className="btn btn--primary btn--sm"
                onClick={() => handleCreateRun('action')}
              >
                + Action Run
              </button>
            )}
          </div>
        </div>
        <div className="card__body">
          {runs.length === 0 ? (
            <div className="empty">暂无执行记录</div>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map(run => (
                    <tr key={run.id}>
                      <td>#{run.id}</td>
                      <td>
                        <span className={`badge badge--${run.run_type}`}>
                          {run.run_type === 'proof' ? 'Proof' : 'Action'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge--${run.status}`}>
                          {run.status}
                        </span>
                      </td>
                      <td>{formatDate(run.created_at)}</td>
                      <td>
                        <span
                          className="link"
                          onClick={() => navigate(`/runs/${run.id}`)}
                        >
                          查看日志
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
