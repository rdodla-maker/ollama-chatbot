import Topbar from '../components/Topbar'
import StatCard from '../components/StatCard'

export default function Dashboard({ status, trackerItems = [], onNavigate }) {
  const recentItems = trackerItems.slice(0, 5)
  const counts = {
    applied: trackerItems.filter((item) => item.status === 'applied').length,
    pending: trackerItems.filter((item) => item.status === 'pending').length,
    interviews: trackerItems.filter((item) => item.status === 'interview').length,
    rejected: trackerItems.filter((item) => item.status === 'rejected').length,
  }

  const hasApplications = trackerItems.length > 0
  const totalApplications = trackerItems.length

  return (
    <div className="page page-wide">
      <Topbar
        title="Dashboard"
        subtitle="Your AI Job Application Assistant"
        status={status}
      />

      {/* Premium Hero Section */}
      <section className="hero-card dashboard-hero-card premium-hero">
        <div className="hero-content">
          <div className="hero-main">
            <p className="eyebrow">AI-Powered Job Search</p>
            <h1 className="hero-headline">Land More Interviews With AI</h1>
            <p className="hero-subtitle">
              Upload your resume, choose job roles, and let AI automate your job search.
            </p>
            <div className="hero-actions">
              <button type="button" className="btn-primary btn-primary-large" onClick={() => onNavigate?.('resume')}>
                Start Apply
              </button>
              {hasApplications && (
                <button type="button" className="btn-ghost" onClick={() => onNavigate?.('applications')}>
                  View Applications
                </button>
              )}
            </div>
            {hasApplications && (
              <div className="hero-stats-inline">
                <span className="hero-stat">
                  <strong>{totalApplications}</strong> {totalApplications === 1 ? 'Application' : 'Applications'} Tracked
                </span>
                <span className="hero-stat-divider">•</span>
                <span className="hero-stat">
                  <strong>{counts.interviews}</strong> {counts.interviews === 1 ? 'Interview' : 'Interviews'}
                </span>
              </div>
            )}
          </div>

          {hasApplications && (
            <div className="hero-aside panel-inset">
              <div className="hero-aside-header">
                <span className="section-kicker">How it works</span>
              </div>
              <div className="activity-list">
                <div className="activity-item">
                  <span className="activity-dot glow-cyan" />
                  <div>
                    <strong>1. Upload resume</strong>
                    <span>Add your latest resume in a few clicks.</span>
                  </div>
                </div>
                <div className="activity-item">
                  <span className="activity-dot glow-purple" />
                  <div>
                    <strong>2. Add job titles</strong>
                    <span>Choose the roles you want the AI to target.</span>
                  </div>
                </div>
                <div className="activity-item">
                  <span className="activity-dot glow-blue" />
                  <div>
                    <strong>3. Track progress</strong>
                    <span>Keep applications organized in one place.</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* First-Time User Onboarding */}
      {!hasApplications && (
        <section className="onboarding-card panel-card">
          <div className="onboarding-content">
            <div className="onboarding-icon">🚀</div>
            <h3>Welcome to Your AI Job Assistant</h3>
            <p>
              Get started in minutes. Upload your resume, select the job roles you're targeting, 
              and let AI handle the heavy lifting of job applications.
            </p>
            <div className="onboarding-features">
              <div className="onboarding-feature">
                <span className="feature-icon">✓</span>
                <span>AI-optimized applications</span>
              </div>
              <div className="onboarding-feature">
                <span className="feature-icon">✓</span>
                <span>Automated job matching</span>
              </div>
              <div className="onboarding-feature">
                <span className="feature-icon">✓</span>
                <span>Track everything in one place</span>
              </div>
            </div>
            <button type="button" className="btn-primary btn-primary-large" onClick={() => onNavigate?.('resume')}>
              Get Started
            </button>
          </div>
        </section>
      )}

      {/* Quick Actions - Only show when user has applications */}
      {hasApplications && (
        <section className="quick-actions-section">
          <h3 className="section-title">Quick Actions</h3>
          <div className="quick-actions-grid-dashboard">
            <button 
              type="button" 
              className="quick-action-card action-card-interactive"
              onClick={() => onNavigate?.('resume')}
            >
              <div className="quick-action-icon">📄</div>
              <strong>Start Apply</strong>
              <span>Upload resume and apply to new roles</span>
            </button>
            <button 
              type="button" 
              className="quick-action-card action-card-interactive"
              onClick={() => onNavigate?.('applications')}
            >
              <div className="quick-action-icon">📊</div>
              <strong>View Applications</strong>
              <span>Track all your job applications</span>
            </button>
            <button 
              type="button" 
              className="quick-action-card action-card-interactive"
              onClick={() => onNavigate?.('resume')}
            >
              <div className="quick-action-icon">✏️</div>
              <strong>Update Resume</strong>
              <span>Replace or optimize your resume</span>
            </button>
          </div>
        </section>
      )}

      {/* Stats Grid - Only show when user has applications */}
      {hasApplications && (
        <section className="stats-grid">
          <StatCard label="Applied" value={counts.applied} detail="Applications sent" tone="cyan" />
          <StatCard label="Pending" value={counts.pending} detail="Being prepared" tone="purple" />
          <StatCard label="Interviews" value={counts.interviews} detail="In progress" tone="blue" />
          <StatCard label="Rejected" value={counts.rejected} detail="Closed" tone="danger" />
        </section>
      )}

      {/* Recent Applications - Only show when user has applications */}
      {hasApplications && (
        <section className="panel-card recent-applications-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Recent activity</span>
              <h3>Latest applications</h3>
            </div>
            <button 
              type="button" 
              className="btn-ghost btn-small"
              onClick={() => onNavigate?.('applications')}
            >
              View All
            </button>
          </div>
          {recentItems.length === 0 ? (
            <p className="muted-block">No recent applications.</p>
          ) : (
            <div className="tracker-table">
              <div className="tracker-row tracker-head">
                <span>Company</span>
                <span>Role</span>
                <span>Status</span>
                <span>Date</span>
              </div>
              {recentItems.map((item, index) => (
                <div key={`${item.company}-${item.role}-${index}`} className="tracker-row">
                  <span>{item.company}</span>
                  <span>{item.role}</span>
                  <span className={`tracker-badge status-${item.status}`}>{item.status}</span>
                  <span>{item.application_date}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
