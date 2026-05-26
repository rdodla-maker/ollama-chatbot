import { useState } from 'react'
import MessageList from './MessageList'
import ReasoningTrace from './ReasoningTrace'
import PendingChanges from './PendingChanges'
import { sendAgent, streamAgent, indexCodebase } from '../api/client'

export default function AgentPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastReasoning, setLastReasoning] = useState([])
  const [lastPlan, setLastPlan] = useState('')
  const [indexing, setIndexing] = useState(false)
  const [useStream, setUseStream] = useState(true)
  const [pendingRefresh, setPendingRefresh] = useState(0)

  const handleSend = async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setError(null)
    setLoading(true)
    setLastReasoning([])
    setLastPlan('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])

    if (useStream) {
      let aiText = ''
      const reasoning = []
      setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

      streamAgent(text, {
        onPlan: (plan) => setLastPlan(plan),
        onReasoning: (step) => {
          reasoning.push(step)
          setLastReasoning([...reasoning])
        },
        onToken: (token) => {
          aiText += token
          setMessages((prev) => {
            const next = [...prev]
            next[next.length - 1] = { role: 'assistant', content: aiText }
            return next
          })
        },
        onDone: () => {
          setLoading(false)
          setPendingRefresh((k) => k + 1)
        },
        onError: (msg) => {
          setError(msg)
          setLoading(false)
        },
      })
      return
    }

    try {
      const data = await sendAgent(text)
      setLastReasoning(data.reasoning || [])
      setLastPlan(data.plan || '')
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response },
      ])
      setPendingRefresh((k) => k + 1)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Agent failed')
    } finally {
      setLoading(false)
    }
  }

  const handleIndexCodebase = async () => {
    setIndexing(true)
    setError(null)
    try {
      const data = await indexCodebase()
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Codebase indexed: ${data.message} (${data.chunks} chunks from ${data.files} files)`,
        },
      ])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Index failed')
    } finally {
      setIndexing(false)
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Autonomous Agent</h2>
        <div className="header-actions">
          <label className="stream-toggle">
            <input
              type="checkbox"
              checked={useStream}
              onChange={(e) => setUseStream(e.target.checked)}
            />
            Stream
          </label>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleIndexCodebase}
            disabled={indexing || loading}
          >
            {indexing ? 'Indexing…' : 'Index codebase'}
          </button>
        </div>
      </div>

      <PendingChanges refreshKey={pendingRefresh} />
      <ReasoningTrace reasoning={lastReasoning} plan={lastPlan} />
      <MessageList messages={messages} />

      {error && (
        <div className="error-banner">
          {error}
          <button type="button" onClick={() => setError(null)}>
            Dismiss
          </button>
        </div>
      )}

      <div className="input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Ask the agent — it can use tools, propose file edits, search code…"
          rows={2}
          disabled={loading}
        />
        <button
          type="button"
          className="btn-primary"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Agent working…' : 'Run agent'}
        </button>
      </div>
    </div>
  )
}
