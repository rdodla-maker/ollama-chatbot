const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: '◆', hint: 'Overview' },
  { id: 'applications', label: 'Job Applications', icon: '◧', hint: 'Create' },
  { id: 'resume', label: 'Resume Analyzer', icon: '△', hint: 'Improve' },
  { id: 'cover-letter', label: 'Cover Letters', icon: '✦', hint: 'Refine' },
  { id: 'tracker', label: 'Application Tracker', icon: '◎', hint: 'Track' },
]

export default function Sidebar({ page, onNavigate, collapsed, onToggle, status }) {
  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="sidebar-brand panel-inset">
        <span className="brand-icon">◈</span>
        {!collapsed && (
          <div className="brand-copy">
            <strong>JobPilot AI</strong>
            <span className="brand-sub">Application assistant</span>
          </div>
        )}
      </div>

      {!collapsed && (
        <div className="sidebar-user panel-inset">
          <div className="sidebar-user-row">
            <div className="sidebar-avatar">JP</div>
            <div>
              <div className="sidebar-user-name">Personal workspace</div>
              <div className="sidebar-user-meta">Solo founder mode</div>
            </div>
          </div>
          <div className="sidebar-status-row">
            <span className={`sidebar-dot ${status?.online ? 'online' : 'offline'}`} />
            <span>{status?.online ? 'AI backend connected' : 'Backend unavailable'}</span>
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        {NAV.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-item ${page === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
            title={item.label}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && (
              <span className="nav-copy">
                <span className="nav-label">{item.label}</span>
                <span className="nav-hint">{item.hint}</span>
              </span>
            )}
          </button>
        ))}
      </nav>

      <button
        type="button"
        className="sidebar-toggle"
        onClick={onToggle}
        title={collapsed ? 'Expand' : 'Collapse'}
      >
        {collapsed ? 'Expand' : 'Collapse'}
      </button>
    </aside>
  )
}
