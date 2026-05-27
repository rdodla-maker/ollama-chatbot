const LABELS = {
  n8n_monitoring: 'n8n monitoring',
  automation_queue: 'automation queue',
  scheduled_workflows: 'scheduled workflows',
  background_jobs: 'background jobs',
}

export default function AutomationReadiness({ placeholders = {}, queue, transport }) {
  const entries = Object.entries(placeholders)

  return (
    <div className="automation-grid">
      {entries.map(([key, value]) => (
        <div key={key} className="automation-card">
          <span className="section-kicker">Placeholder</span>
          <strong>{LABELS[key] || key}</strong>
          <p>{String(value).replaceAll('_', ' ')}</p>
        </div>
      ))}
      <div className="automation-card automation-card-highlight">
        <span className="section-kicker">Queue preview</span>
        <strong>{queue?.size || 0} pending actions</strong>
        <p>
          {(queue?.pending || []).length
            ? (queue.pending || []).map((item) => item.type).join(', ')
            : 'No pending background jobs in the in-memory queue.'}
        </p>
      </div>
      <div className="automation-card automation-card-highlight">
        <span className="section-kicker">Transport readiness</span>
        <strong>{transport?.mode || 'polling'}</strong>
        <p>{(transport?.supported || []).join(', ') || 'Polling only'}</p>
      </div>
    </div>
  )
}