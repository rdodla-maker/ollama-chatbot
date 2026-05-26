import { useState } from 'react'
import MessageList from './MessageList'
import { sendChat, streamChat } from '../api/client'

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [useStream, setUseStream] = useState(true)

  const handleSend = async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setError(null)
    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', content: text }])

    if (useStream) {
      let aiText = ''
      setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

      streamChat(text, {
        onToken: (token) => {
          aiText += token
          setMessages((prev) => {
            const next = [...prev]
            next[next.length - 1] = { role: 'assistant', content: aiText }
            return next
          })
        },
        onDone: () => setLoading(false),
        onError: (msg) => {
          setError(msg)
          setLoading(false)
        },
      })
      return
    }

    try {
      const data = await sendChat(text)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response },
      ])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>PDF Chat (RAG)</h2>
        <label className="stream-toggle">
          <input
            type="checkbox"
            checked={useStream}
            onChange={(e) => setUseStream(e.target.checked)}
          />
          Stream
        </label>
      </div>

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
          placeholder="Ask about your uploaded PDFs..."
          rows={2}
          disabled={loading}
        />
        <button
          type="button"
          className="btn-primary"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Thinking…' : 'Send'}
        </button>
      </div>
    </div>
  )
}
