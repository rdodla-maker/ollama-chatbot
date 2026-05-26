export default function AgentReasoning({ steps, collapsed, onToggle }) {
  if (!steps?.length) {
    return (
      <div className="panel-card">
        <div className="panel-card-header">
          <h3>Reasoning</h3>
        </div>
        <p className="panel-muted">No reasoning steps yet.</p>
      </div>
    )
  }

  return (
    <div className="panel-card">
      <button type="button" className="panel-card-header clickable" onClick={onToggle}>
        <h3>Reasoning</h3>
        <span className="chevron">{collapsed ? '▸' : '▾'}</span>
      </button>
      {!collapsed && (
        <ol className="reasoning-list">
          {steps.map((step, i) => (
            <li key={i} className={i === steps.length - 1 ? 'active' : ''}>
              {step}
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
