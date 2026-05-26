export default function Topbar({ title, subtitle, status, onClear, clearLabel = 'Clear' }) {
  return (
    <header className="topbar">
      <div>
        <h1 className="topbar-title">{title}</h1>
        {subtitle && <p className="topbar-sub">{subtitle}</p>}
      </div>
      <div className="topbar-actions">
        {status && (
          <span className={`status-pill ${status.online ? 'online' : 'offline'}`}>
            {status.label}
          </span>
        )}
        {onClear && (
          <button type="button" className="btn-ghost" onClick={onClear}>
            {clearLabel}
          </button>
        )}
      </div>
    </header>
  )
}
