export default function Topbar({ title, subtitle, status, onClear, clearLabel = 'Clear' }) {
  return (
    <header className="topbar">
      <div className="topbar-copy">
        <div className="topbar-eyebrow">AI Job Application Assistant</div>
        <h1 className="topbar-title">{title}</h1>
        {subtitle && <p className="topbar-sub">{subtitle}</p>}
      </div>
      <div className="topbar-actions">
        <div className="topbar-search">
          <span className="topbar-search-icon">⌕</span>
          <input type="text" placeholder="Search jobs, drafts, companies..." aria-label="Search placeholder" readOnly />
        </div>
        {status && (
          <span className={`status-pill ${status.online ? 'online' : 'offline'}`}>
            {status.label}
          </span>
        )}
        <div className="topbar-profile">
          <div className="topbar-profile-copy">
            <strong>Founder</strong>
            <span>Workspace owner</span>
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
