import { useCallback, useEffect, useState } from 'react'
import {
  approveChange,
  fetchPendingChanges,
  rejectChange,
} from '../api/client'

export default function PendingChanges({ refreshKey = 0 }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchPendingChanges()
      setItems(data)
    } catch (err) {
      setError(err.message || 'Failed to load pending changes')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load, refreshKey])

  const handleApprove = async (id) => {
    try {
      await approveChange(id)
      await load()
    } catch (err) {
      setError(err.message || 'Approve failed')
    }
  }

  const handleReject = async (id) => {
    try {
      await rejectChange(id)
      await load()
    } catch (err) {
      setError(err.message || 'Reject failed')
    }
  }

  if (!items.length && !loading && !error) {
    return null
  }

  return (
    <div className="pending-panel">
      <div className="pending-header">
        <h3>Pending file edits</h3>
        <button type="button" className="btn-secondary" onClick={load} disabled={loading}>
          Refresh
        </button>
      </div>
      {error && <div className="error-banner">{error}</div>}
      {loading && <p className="muted">Loading…</p>}
      <ul className="pending-list">
        {items.map((item) => (
          <li key={item.id} className="pending-item">
            <div>
              <strong>{item.file_path}</strong>
              <span className="pending-id">#{item.id}</span>
            </div>
            <pre className="pending-preview">{item.preview}</pre>
            <div className="pending-actions">
              <button
                type="button"
                className="btn-primary"
                onClick={() => handleApprove(item.id)}
              >
                Approve
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleReject(item.id)}
              >
                Reject
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
