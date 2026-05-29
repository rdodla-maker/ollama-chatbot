/**
 * EmptyState Component
 * Reusable empty state display with icon, title, description, and optional action
 */

export default function EmptyState({ 
  icon, 
  title, 
  description, 
  action,
  actionLabel,
  onAction,
  variant = 'default' // 'default' | 'compact'
}) {
  // Compact variant for inline empty states
  if (variant === 'compact') {
    return (
      <p className="muted-block section-empty">
        {description || title}
      </p>
    )
  }

  // Full variant for page-level empty states
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon">{icon}</div>}
      {title && <h3>{title}</h3>}
      {description && <p>{description}</p>}
      {action && onAction && (
        <button type="button" className="btn-primary" onClick={onAction}>
          {actionLabel || action}
        </button>
      )}
    </div>
  )
}
