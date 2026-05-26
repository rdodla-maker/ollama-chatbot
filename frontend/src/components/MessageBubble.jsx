import { useState } from 'react'

function renderContent(text) {
  if (!text) return null
  const parts = text.split(/(```[\s\S]*?```)/g)
  return parts.map((part, i) => {
    if (part.startsWith('```')) {
      const code = part.replace(/^```\w*\n?/, '').replace(/```$/, '')
      return (
        <pre key={i} className="code-block">
          <code>{code}</code>
        </pre>
      )
    }
    return (
      <span key={i} className="text-block">
        {part.split('\n').map((line, j, arr) => (
          <span key={j}>
            {line}
            {j < arr.length - 1 && <br />}
          </span>
        ))}
      </span>
    )
  })
}

export default function MessageBubble({ message }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* ignore */
    }
  }

  return (
    <div className={`bubble-row ${isUser ? 'bubble-row-user' : 'bubble-row-ai'}`}>
      <div className={`bubble ${isUser ? 'bubble-user' : 'bubble-ai'}`}>
        <div className="bubble-meta">
          <span className="bubble-role">{isUser ? 'You' : 'AI'}</span>
          {!isUser && message.content && (
            <button type="button" className="bubble-copy" onClick={copy}>
              {copied ? 'Copied' : 'Copy'}
            </button>
          )}
        </div>
        <div className="bubble-content">
          {message.streaming && !message.content ? (
            <span className="typing-cursor">▋</span>
          ) : (
            renderContent(message.content)
          )}
        </div>
      </div>
    </div>
  )
}
