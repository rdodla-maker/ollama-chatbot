export default function ExecutionPlan({ plan, steps, collapsed, onToggle }) {
  const hasPlan = plan?.trim()

  return (
    <div className="panel-card">
      <button type="button" className="panel-card-header clickable" onClick={onToggle}>
        <h3>Execution plan</h3>
        <span className="chevron">{collapsed ? '▸' : '▾'}</span>
      </button>
      {!collapsed && (
        <>
          {steps?.length > 0 ? (
            <ol className="plan-steps">
              {steps.map((step, i) => (
                <li key={i}>{step.replace(/^\d+[\.\)]\s*/, '')}</li>
              ))}
            </ol>
          ) : hasPlan ? (
            <pre className="plan-raw">{plan}</pre>
          ) : (
            <p className="panel-muted">Plan will appear when the agent runs.</p>
          )}
        </>
      )}
    </div>
  )
}
