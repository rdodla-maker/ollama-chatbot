export default function MessageList({ messages }) {
  if (!messages.length) {
    return (
      <div className="empty-state">
        <p>No messages yet. Start a conversation below.</p>
      </div>
    )
  }

  return (
    <div className="message-list">
      {messages.map((msg, i) => (
        <div key={i} className={`message message-${msg.role}`}>
          <span className="message-role">
            {msg.role === 'user' ? 'You' : 'AI'}
          </span>
          <div className="message-content">{msg.content}</div>
        </div>
      ))}
    </div>
  )
}
