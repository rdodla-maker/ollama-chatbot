function formatTime(value) {
  if (!value) return 'Pending'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Pending'
  return date.toLocaleString()
}

function formatDuration(seconds) {
  if (seconds == null) return 'Live'
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${(seconds / 3600).toFixed(1)}h`
}

export default function WorkflowTimeline({ timeline = [] }) {
  if (!timeline.length) {
    return <p className="muted-block">Timeline will appear as the AI workflow progresses.</p>
  }

  return (
    <div className="workflow-timeline">
      {timeline.map((event, index) => (
        <div key={`${event.stage}-${event.timestamp || index}`} className="timeline-item">
          <div className="timeline-rail">
            <span className={`timeline-dot state-${event.state}`} />
            {index < timeline.length - 1 ? <span className="timeline-line" /> : null}
          </div>
          <div className="timeline-content">
            <div className="timeline-head">
              <strong>{event.label}</strong>
              <span className={`mission-badge tone-${event.state}`}>{event.state}</span>
            </div>
            <div className="timeline-meta">
              <span>{formatTime(event.timestamp)}</span>
              <span>{formatDuration(event.duration_seconds)}</span>
            </div>
            <div className="timeline-log">Source: {event.metadata?.source || 'workflow-engine'}</div>
            <div className="timeline-log">Event: {event.metadata?.event_type || event.status}</div>
            {event.metadata?.severity ? <div className="timeline-log">Severity: {event.metadata.severity}</div> : null}
            {event.metadata?.owner ? <div className="timeline-log">Owner: {event.metadata.owner}</div> : null}
            {event.metadata?.previous_stage ? <div className="timeline-log">Previous stage: {event.metadata.previous_stage}</div> : null}
            {event.metadata?.worker_owner ? <div className="timeline-log">Worker: {event.metadata.worker_owner}</div> : null}
            {event.metadata?.reason ? <div className="timeline-log">Reason: {event.metadata.reason}</div> : null}
            {event.metadata?.retry_count ? <div className="timeline-log">Retry attempt {event.metadata.retry_count}</div> : null}
            {event.metadata?.resume_stage ? <div className="timeline-log">Resume stage: {event.metadata.resume_stage}</div> : null}
            {event.metadata?.action ? <div className="timeline-log">Action: {event.metadata.action}</div> : null}
          </div>
        </div>
      ))}
    </div>
  )
}