export default function LoadingIndicator({ label = 'Thinking' }) {
  return (
    <div className="loading-indicator" aria-live="polite">
      <span className="loading-dots">
        <span />
        <span />
        <span />
      </span>
      <span className="loading-label">{label}</span>
    </div>
  )
}
