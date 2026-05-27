function formatDuration(seconds) {
  if (seconds == null) return 'In progress'
  if (seconds < 60) return `${Math.round(seconds)} sec`
  if (seconds < 3600) return `${Math.round(seconds / 60)} min`
  return `${(seconds / 3600).toFixed(1)} hr`
}

function formatAgo(value) {
  if (!value) return 'No activity yet'
  const timestamp = new Date(value).getTime()
  if (Number.isNaN(timestamp)) return 'No activity yet'
  const diff = Math.max(Date.now() - timestamp, 0)
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hr ago`
  return `${Math.floor(hours / 24)} d ago`
}

export default function WorkflowCard({ workflow, selected, onSelect, onAction, actionLoading }) {
  function handleKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onSelect?.(workflow.id)
    }
  }

  return (
    <div
      className={`workflow-card ${selected ? 'selected' : ''} state-${workflow.current_stage_state}`}
      onClick={() => onSelect?.(workflow.id)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-pressed={selected}
    >
      <div className="workflow-card-head">
        <div>
          <span className="section-kicker">Workflow {workflow.id?.slice(0, 8) || 'local'}</span>
          <h4>{workflow.current_stage_label}</h4>
        </div>
        <span className={`mission-badge tone-${workflow.current_stage_state}`}>{workflow.current_stage_state}</span>
      </div>
      <p className="workflow-card-file">{workflow.uploaded_filename}</p>
      <div className="workflow-progress-bar" aria-hidden="true">
        <span style={{ width: `${workflow.progress_percentage || 0}%` }} />
      </div>
      <div className="workflow-card-stats">
        <div>
          <span className="workflow-stat-label">ATS</span>
          <strong>{workflow.ats_score ?? '--'}</strong>
        </div>
        <div>
          <span className="workflow-stat-label">Progress</span>
          <strong>{workflow.progress_percentage || 0}%</strong>
        </div>
        <div>
          <span className="workflow-stat-label">Duration</span>
          <strong>{formatDuration(workflow.workflow_duration_seconds)}</strong>
        </div>
      </div>
      <div className="workflow-card-footer">
        <div className="pill-stack">
          {(workflow.target_roles || []).slice(0, 2).map((role) => (
            <span key={role} className="soft-pill">{role}</span>
          ))}
          {(workflow.target_roles || []).length > 2 ? <span className="soft-pill">+{workflow.target_roles.length - 2}</span> : null}
        </div>
        <span className="workflow-last-activity">{formatAgo(workflow.last_activity)}</span>
      </div>

      <div className="workflow-action-row" onClick={(event) => event.stopPropagation()}>
        {(workflow.available_actions || []).map((item) => (
          <button
            key={item.action}
            type="button"
            className={`workflow-action-btn ${item.enabled ? '' : 'disabled'} ${item.action === 'cancel' ? 'danger' : ''}`}
            disabled={!item.enabled || actionLoading}
            title={item.reason || item.label}
            onClick={() => onAction?.(workflow.id, item.action)}
          >
            {actionLoading && item.enabled ? 'Working...' : item.label}
          </button>
        ))}
      </div>
    </div>
  )
}