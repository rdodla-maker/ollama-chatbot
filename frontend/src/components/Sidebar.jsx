const NAV = [
  { id: 'chat', label: 'Chat', icon: '💬' },
  { id: 'agent', label: 'Agent', icon: '⚡' },
  { id: 'rag', label: 'PDF RAG', icon: '📄' },
  { id: 'codebase', label: 'Codebase', icon: '🗂️' },
  { id: 'memory', label: 'Memory', icon: '🧠' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
]

export default function Sidebar({ page, onNavigate, collapsed, onToggle }) {
  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="sidebar-brand">
        <span className="brand-icon">◈</span>
        {!collapsed && (
          <div>
            <strong>Local AI</strong>
            <span className="brand-sub">Personal OS</span>
          </div>
        )}
      </div>

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
            {!collapsed && <span className="nav-label">{item.label}</span>}
          </button>
        ))}
      </nav>

      <button
        type="button"
        className="sidebar-toggle"
        onClick={onToggle}
        title={collapsed ? 'Expand' : 'Collapse'}
      >
        {collapsed ? '»' : '«'}
      </button>
    </aside>
  )
}
