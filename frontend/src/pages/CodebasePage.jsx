import { useState } from 'react'
import Topbar from '../components/Topbar'
import ChatWindow from '../components/ChatWindow'
import { indexCodebase } from '../api/api'
import { useAgent } from '../hooks/useAgent'

export default function CodebasePage({ status }) {
  const { messages, loading, sendMessage, clearSession, reasoning, plan } = useAgent({ stream: true })
  const [indexing, setIndexing] = useState(false)
  const [indexMsg, setIndexMsg] = useState(null)

  const handleIndex = async () => {
    setIndexing(true)
    setIndexMsg(null)
    try {
      const data = await indexCodebase()
      setIndexMsg(data.message || `Indexed ${data.chunks} chunks`)
    } catch (err) {
      setIndexMsg(err.response?.data?.detail || err.message || 'Index failed')
    } finally {
      setIndexing(false)
    }
  }

  return (
    <div className="page page-codebase">
      <Topbar
        title="Codebase AI"
        subtitle="Index repository · semantic search · architecture analysis"
        status={status}
        onClear={clearSession}
        clearLabel="Clear"
      />
      <div className="codebase-toolbar">
        <button type="button" className="btn-primary" onClick={handleIndex} disabled={indexing}>
          {indexing ? 'Indexing…' : 'Index codebase'}
        </button>
        {indexMsg && <span className="toolbar-msg">{indexMsg}</span>}
      </div>
      <div className="codebase-hints">
        <p>Try: <code>search codebase for FastAPI routes</code> · <code>analyze project backend</code></p>
      </div>
      <ChatWindow
        messages={messages}
        loading={loading}
        onSend={sendMessage}
        placeholder="Search code, analyze architecture, read files…"
        emptyTitle="Codebase intelligence"
        emptyDescription="Index your repo first, then ask the agent to explore your code."
      />
      {(reasoning.length > 0 || plan) && (
        <div className="codebase-meta">
          {plan && <pre className="plan-snippet">{plan.slice(0, 400)}…</pre>}
        </div>
      )}
    </div>
  )
}
