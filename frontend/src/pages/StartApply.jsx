import Topbar from '../components/Topbar'
import StartApplyWizard from '../components/StartApplyWizard'

export default function StartApply({ onNavigate }) {
  return (
    <div className="page page-wide">
      <Topbar title="Start Apply" subtitle="Upload your resume and target roles to begin." />
      <section className="panel-card">
        <StartApplyWizard onDone={() => onNavigate?.('tracker')} />
      </section>
    </div>
  )
}
