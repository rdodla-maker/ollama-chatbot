import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar'
import StatCard from '../components/StatCard'
import { fetchTrackerItems } from '../services/trackerService'

export default function ApplicationTracker({ status, onTrackerLoaded }) {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    let mounted = true

    async function loadTracker() {
      setLoading(true)
      setError('')
      try {
        const items = await fetchTrackerItems()
        if (!mounted) return
        setApplications(items)
        onTrackerLoaded?.(items)
      } catch (err) {
        if (!mounted) return
        setError(err.response?.data?.detail || err.message || 'Failed to load tracker.')
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadTracker()
    return () => {
      mounted = false
    }
  }, [onTrackerLoaded])

  const counts = {
    applied: applications.filter((item) => item.status === 'applied').length,
    pending: applications.filter((item) => item.status === 'pending').length,
    interviews: applications.filter((item) => item.status === 'interview').length,
    rejected: applications.filter((item) => item.status === 'rejected').length,
  }

  const filteredApplications = applications.filter((item) => {
    const matchesFilter = filter === 'all' ? true : item.status === filter
    const haystack = `${item.company} ${item.role}`.toLowerCase()
    const matchesQuery = haystack.includes(query.trim().toLowerCase())
    return matchesFilter && matchesQuery
  })

  return (
    <div className="page page-wide">
      <Topbar
        title="Application Tracker"
        subtitle="See generated applications grouped by their current status."
        status={status}
      />

      <section className="stats-grid">
        <StatCard label="Applied" value={counts.applied} tone="cyan" />
        <StatCard label="Pending" value={counts.pending} tone="purple" />
        <StatCard label="Interviews" value={counts.interviews} tone="blue" />
        <StatCard label="Rejected" value={counts.rejected} tone="danger" />
      </section>

      <div className="panel-card">
        <div className="panel-card-header">
          <div>
            <span className="section-kicker">Pipeline</span>
            <h3>Tracked jobs</h3>
          </div>
          <div className="tracker-toolbar">
            <div className="topbar-search tracker-search">
              <span className="topbar-search-icon">⌕</span>
              <input
                type="text"
                placeholder="Search company or role"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <select className="tracker-filter" value={filter} onChange={(event) => setFilter(event.target.value)}>
              <option value="all">All statuses</option>
              <option value="pending">Pending</option>
              <option value="applied">Applied</option>
              <option value="interview">Interview</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
        {loading ? <p className="muted-block">Loading tracker...</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
        {!loading && applications.length === 0 ? (
          <p className="muted-block">No applications tracked yet. Generate your first application pack.</p>
        ) : null}
        {filteredApplications.length > 0 ? (
          <div className="tracker-table">
            <div className="tracker-row tracker-head">
              <span>Company</span>
              <span>Role</span>
              <span>Date</span>
              <span>Status</span>
            </div>
            {filteredApplications.map((item, index) => (
              <div key={`${item.company}-${item.role}-${index}`} className="tracker-row">
                <span>{item.company}</span>
                <span>{item.role}</span>
                <span>{item.application_date}</span>
                <span className={`tracker-badge status-${item.status}`}>{item.status}</span>
              </div>
            ))}
          </div>
        ) : (!loading && applications.length > 0 ? <p className="muted-block">No applications match your current filter.</p> : null)}
      </div>
    </div>
  )
}
