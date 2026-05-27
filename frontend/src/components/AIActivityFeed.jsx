function formatTime(value) {
  if (!value) return 'Live'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Live'
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function AIActivityFeed({ activity = [] }) {
  if (!activity.length) {
    return <p className="muted-block">Recent AI activity will populate as workflows move through each stage.</p>
  }

  return (
    <div className="mission-feed">
      {activity.map((item, index) => (
        <div key={`${item.workflow_id}-${item.timestamp || index}`} className="mission-feed-item">
          <span className={`activity-dot state-${item.state}`} />
          <div className="mission-feed-copy">
            <strong>{item.label}</strong>
            <span>{item.filename} · {item.source} · {item.event_type}</span>
          </div>
          <div className="mission-feed-meta">
            <span className={`mission-badge tone-${item.state}`}>{item.state}</span>
            <span>{formatTime(item.timestamp)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}