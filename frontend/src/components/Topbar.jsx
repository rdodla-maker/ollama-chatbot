export default function Topbar({ title, subtitle, status, onClear, clearLabel = 'Clear' }) {
  return (
    <header className="topbar">
      <div className="topbar-copy">
        <div className="topbar-eyebrow">Career Copilot</div>
        <h1 className="topbar-title">{title}</h1>
        {subtitle && <p className="topbar-sub">{subtitle}</p>}
      </div>
      <div className="topbar-actions">
        {status && (
          <span className={`status-pill ${status.online ? 'online' : 'offline'}`}>
            {status.label}
          </span>
        )}
        <div className="topbar-profile">
          <div className="topbar-profile-copy">
            <strong>You</strong>
            <span>Personal workspace</span>
          </div>
          <div className="topbar-avatar">AI</div>
        </div>
        {onClear && (
          <button type="button" className="btn-ghost" onClick={onClear}>
            {clearLabel}
          </button>
        )}
      </div>
    </header>
  )
}
