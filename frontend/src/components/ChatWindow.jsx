import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import LoadingIndicator from './LoadingIndicator'
import EmptyState from './EmptyState'

export default function ChatWindow({
  messages,
  loading,
  onSend,
  placeholder = 'Message your AI…',
  emptyTitle = 'Start a conversation',
  emptyDescription = 'Ask anything. Your messages appear here.',
}) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = (e) => {
    e?.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    onSend(text)
  }

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 && !loading && (
          <EmptyState
            icon="✦"
            title={emptyTitle}
            description={emptyDescription}
          />
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {loading && messages[messages.length - 1]?.role !== 'assistant' && (
          <LoadingIndicator />
        )}
        <div ref={bottomRef} />
      </div>

      <form className="chat-composer" onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit()
            }
          }}
          placeholder={placeholder}
          rows={1}
          disabled={loading}
        />
        <button type="submit" className="btn-send" disabled={loading || !input.trim()}>
          {loading ? '…' : '↑'}
        </button>
      </form>
    </div>
  )
}
