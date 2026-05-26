export default function ToolActivity({ tools, pending = [] }) {
  const hasTools = tools?.length > 0
  const hasPending = pending?.length > 0

  if (!hasTools && !hasPending) {
    return (
      <div className="panel-card">
        <div className="panel-card-header">
          <h3>Tool activity</h3>
        </div>
        <p className="panel-muted">Tools will show here when used.</p>
      </div>
    )
  }

  return (
    <div className="panel-card">
      <div className="panel-card-header">
        <h3>Tool activity</h3>
      </div>
      {hasTools && (
        <ul className="tool-list">
          {tools.map((t, i) => (
            <li key={i} className="tool-item">
              <span className="tool-badge">{t.name}</span>
              <span className="tool-args">{t.args}</span>
            </li>
          ))}
        </ul>
      )}
      {hasPending && (
        <div className="pending-tools">
          <p className="panel-subtitle">Pending approvals</p>
          {pending.map((p) => (
            <div key={p.id} className="pending-item-mini">
              <code>{p.file_path}</code>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
