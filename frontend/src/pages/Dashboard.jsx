import Topbar from '../components/Topbar'
import StatCard from '../components/StatCard'

export default function Dashboard({ status, latestResult, trackerItems = [], onNavigate }) {
  const pendingCount = trackerItems.filter((item) => item.status === 'pending').length
  const recentItems = trackerItems.slice(0, 3)

  return (
    <div className="page page-wide">
      <Topbar
        title="Dashboard"
        subtitle="Generate tailored application materials and track them in one place."
        status={status}
      />

      <section className="hero-card">
        <div className="hero-grid">
          <div>
            <p className="eyebrow">AI Job Application Assistant</p>
            <h2>Build a standout application pack with startup-grade polish.</h2>
            <p>
              Turn one job brief into a tailored outreach email, polished cover letter,
              and resume improvement plan in a single workflow.
            </p>
            <div className="hero-actions">
              <button type="button" className="btn-primary" onClick={() => onNavigate?.('start-apply')}>
                Start Apply
              </button>
              <button type="button" className="btn-ghost" onClick={() => onNavigate?.('tracker')}>
                Open Tracker
              </button>
            </div>
          </div>

          <div className="hero-aside panel-inset">
            <div className="hero-aside-header">
              <span className="section-kicker">AI activity</span>
              <span className={`status-pill ${status?.online ? 'online' : 'offline'}`}>{status?.label}</span>
            </div>
            <div className="activity-list">
              <div className="activity-item">
                <span className="activity-dot glow-cyan" />
                <div>
                  <strong>Email drafting</strong>
                  <span>Role-aware outreach copy generated in seconds.</span>
                </div>
              </div>
              <div className="activity-item">
                <span className="activity-dot glow-purple" />
                <div>
                  <strong>Cover letter tuning</strong>
                  <span>Structured for clarity, tone, and fit.</span>
                </div>
              </div>
              <div className="activity-item">
                <span className="activity-dot glow-blue" />
                <div>
                  <strong>Resume suggestions</strong>
                  <span>Targeted improvement ideas based on the job brief.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="Tracked applications" value={trackerItems.length} detail="Stored locally and ready for Google Sheets sync." tone="cyan" />
        <StatCard label="Pending" value={pendingCount} detail="Generated but not yet moved to interview stage." tone="purple" />
        <StatCard label="Latest email" value={latestResult ? 'Ready' : 'Not generated'} detail="Your newest outreach draft." tone="blue" />
      </section>

      <section className="panel-grid two-column">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Workflow</span>
              <h3>What this MVP does</h3>
            </div>
          </div>
          <ul className="feature-list">
            <li>Collects job and resume details from a single form.</li>
            <li>Uses Ollama to generate an email, cover letter, and resume suggestions.</li>
            <li>Stores application records for the tracker and Google Sheets sync.</li>
          </ul>
        </div>

        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Preview</span>
              <h3>Latest output</h3>
            </div>
          </div>
          <p className="muted-block">
            {latestResult?.generated_cover_letter
              ? latestResult.generated_cover_letter.slice(0, 280) + '...'
              : 'Generate your first application pack to preview outputs here.'}
          </p>
        </div>
      </section>

      <section className="panel-grid two-column dashboard-bottom-grid">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Quick actions</span>
              <h3>Move faster</h3>
            </div>
          </div>
          <div className="quick-actions-grid">
            <button type="button" className="quick-action-card" onClick={() => onNavigate?.('start-apply')}>
              <strong>Start Apply</strong>
              <span>Begin a multi-step resume & role workflow.</span>
            </button>
            <button type="button" className="quick-action-card" onClick={() => onNavigate?.('resume')}>
              <strong>Review resume</strong>
              <span>Open AI suggestions tailored to your latest target role.</span>
            </button>
          </div>
        </div>

        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Recent applications</span>
              <h3>Latest activity</h3>
            </div>
          </div>
          {recentItems.length === 0 ? (
            <p className="muted-block">No applications yet. Your recent jobs will appear here.</p>
          ) : (
            <div className="recent-list">
              {recentItems.map((item, index) => (
                <div key={`${item.company}-${item.role}-${index}`} className="recent-item">
                  <div>
                    <strong>{item.company}</strong>
                    <span>{item.role}</span>
                  </div>
                  <span className={`tracker-badge status-${item.status}`}>{item.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
