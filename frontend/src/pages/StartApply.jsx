import Topbar from '../components/Topbar'
import StartApplyWizard from '../components/StartApplyWizard'

export default function StartApply({ onNavigate }) {
  return (
    <div className="page page-wide">
      <Topbar title="Resume" subtitle="Upload your resume, choose target roles, and start applying." />
      <section className="page-intro-card panel-inset start-apply-intro">
        <div>
          <span className="section-kicker">Start apply</span>
          <h2>One action. A cleaner way to move through your job search.</h2>
        </div>
        <p>
          Upload your resume, add up to five roles, and let the assistant handle the rest in the background.
        </p>
      </section>
      <section className="panel-card">
        <StartApplyWizard onDone={() => onNavigate?.('applications')} />
      </section>
    </div>
  )
}
