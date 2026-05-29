/**
 * ApplicationCard Component
 * Displays a single job application with company, role, status, and metadata
 */

export default function ApplicationCard({ application }) {
  const { company, role, status, source, application_date } = application

  return (
    <div className="application-card panel-inset">
      <div className="application-card-header">
        <h4>{company}</h4>
        <span className={`tracker-badge status-${status}`}>{status}</span>
      </div>
      
      <p className="application-card-role">{role}</p>
      
      <div className="application-card-meta">
        {source && (
          <span className="application-card-source">
            <span className="meta-icon">🔗</span>
            {source}
          </span>
        )}
      </div>
      
      <div className="application-card-footer">
        <span className="application-card-date">
          <span className="meta-icon">📅</span>
          {application_date || '--'}
        </span>
      </div>
    </div>
  )
}
