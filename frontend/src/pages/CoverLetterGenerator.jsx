import Topbar from '../components/Topbar'
import ResultTabs from '../components/ResultTabs'

export default function CoverLetterGenerator({ status, latestResult }) {
  return (
    <div className="page page-wide">
      <Topbar
        title="Cover Letter Generator"
        subtitle="Review and copy your most recent cover letter and outreach email."
        status={status}
      />

      <section className="page-intro-card panel-inset">
        <div>
          <span className="section-kicker">Communication studio</span>
          <h2>Present your story with cleaner, sharper application messaging.</h2>
        </div>
        <p>
          Compare the AI-generated email and cover letter, copy either instantly, and iterate from a polished baseline.
        </p>
      </section>

      <div className="panel-grid two-column analyzer-layout">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Writing principles</span>
              <h3>What strong drafts should do</h3>
            </div>
          </div>
          <div className="quick-actions-grid">
            <div className="quick-action-card static-card">
              <strong>Open with fit</strong>
              <span>Connect your experience to the role within the first few lines.</span>
            </div>
            <div className="quick-action-card static-card">
              <strong>Stay specific</strong>
              <span>Reference outcomes, tools, and business value instead of generic enthusiasm.</span>
            </div>
            <div className="quick-action-card static-card">
              <strong>End with momentum</strong>
              <span>Use a clear close that feels proactive and easy to respond to.</span>
            </div>
          </div>
        </div>

        <ResultTabs results={latestResult} />
      </div>
    </div>
  )
}
