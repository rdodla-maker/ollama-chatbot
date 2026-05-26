export default function ReasoningTrace({ reasoning, plan }) {
  if (!reasoning?.length && !plan) return null

  return (
    <div className="reasoning-panel">
      {plan && (
        <details open>
          <summary>Execution plan</summary>
          <pre className="plan-text">{plan}</pre>
        </details>
      )}
      {reasoning?.length > 0 && (
        <details open>
          <summary>Reasoning steps ({reasoning.length})</summary>
          <ol className="reasoning-list">
            {reasoning.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </details>
      )}
    </div>
  )
}
