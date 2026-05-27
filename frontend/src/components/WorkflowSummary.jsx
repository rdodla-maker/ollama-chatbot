import { useEffect, useState } from 'react'
import { getWorkflowStatus } from '../api/api'

function WorkflowItem({ profile }) {
  return (
    <div className="workflow-item">
      <div className="workflow-main">
        <strong>{profile.uploaded_filename || 'Unnamed'}</strong>
        <span className="muted">{new Date(profile.created_at).toLocaleString()}</span>
      </div>
      <div className={`tracker-badge status-${profile.status || 'unknown'}`}>{profile.status || 'unknown'}</div>
    </div>
  )
}

export default function WorkflowSummary() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    getWorkflowStatus()
      .then((data) => {
        if (!mounted) return
        setItems(data.profiles || [])
      })
      .catch(() => {
        /* ignore */
      })
      .finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  if (loading) return <p className="muted-block">Loading workflow...</p>
  if (!items.length) return <p className="muted-block">No workflow profiles yet.</p>

  return (
    <div className="workflow-list">
      {items.map((p) => (
        <WorkflowItem key={p.id} profile={p} />
      ))}
    </div>
  )
}
