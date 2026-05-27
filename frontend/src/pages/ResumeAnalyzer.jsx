import Topbar from '../components/Topbar'

export default function ResumeAnalyzer({ status, latestResult }) {
  return (
    <div className="page page-wide">
      <Topbar
        title="Resume Analyzer"
        subtitle="Review AI suggestions for improving your resume against a target job."
        status={status}
      />

      <section className="page-intro-card panel-inset">
        <div>
          <span className="section-kicker">Resume intelligence</span>
          <h2>See exactly how to strengthen your resume for the target role.</h2>
        </div>
        <p>
          This workspace turns your latest AI suggestions into a clearer improvement plan so you can refine impact,
          phrasing, and alignment before applying.
        </p>
      </section>

      <div className="panel-grid two-column analyzer-layout">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Checklist</span>
              <h3>Optimization areas</h3>
            </div>
          </div>
          <div className="quick-actions-grid">
            <div className="quick-action-card static-card">
              <strong>Match keywords</strong>
              <span>Mirror the job description with precise technology and domain terms.</span>
            </div>
            <div className="quick-action-card static-card">
              <strong>Quantify outcomes</strong>
              <span>Show business impact with measurable results instead of generic responsibilities.</span>
            </div>
            <div className="quick-action-card static-card">
              <strong>Sharpen summaries</strong>
              <span>Lead with a concise profile that anchors your strongest value for the role.</span>
            </div>
          </div>
        </div>

        <div className="panel-card results-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">AI review</span>
              <h3>Resume suggestions</h3>
            </div>
            <span className="soft-pill accent">Tailored analysis</span>
          </div>
          <div className="result-body result-body-article">
            <pre>
              {latestResult?.resume_suggestions || 'Generate an application pack first to see tailored resume guidance here.'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
