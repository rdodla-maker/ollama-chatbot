import { useCallback, useEffect, useState } from 'react'
import { getMemory } from '../api/api'
import LoadingIndicator from './LoadingIndicator'
import EmptyState from './EmptyState'

export default function MemoryViewer() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getMemory()
      setEntries(data.entries || [])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load memory')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <LoadingIndicator label="Loading memory" />

  if (error) {
    return (
      <div className="banner error">
        {error}
        <button type="button" className="btn-ghost" onClick={load}>
          Retry
        </button>
      </div>
    )
  }

  if (!entries.length) {
    return (
      <EmptyState
        icon="🧠"
        title="No memory yet"
        description="Agent tasks will be saved here after you run the autonomous agent."
      />
    )
  }

  return (
    <div className="memory-viewer">
      <div className="memory-toolbar">
        <span>{entries.length} entries</span>
        <button type="button" className="btn-ghost" onClick={load}>
          Refresh
        </button>
      </div>
      <div className="memory-list">
        {entries.map((entry, i) => (
          <article key={i} className="memory-card">
            <header>
              <time>{entry.timestamp || '—'}</time>
            </header>
            <h4>{entry.task}</h4>
            {entry.plan && (
              <details>
                <summary>Plan</summary>
                <pre>{entry.plan}</pre>
              </details>
            )}
            <p className="memory-result">{entry.result}</p>
          </article>
        ))}
      </div>
    </div>
  )
}
