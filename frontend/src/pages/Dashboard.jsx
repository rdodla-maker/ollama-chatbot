import { useState } from 'react'
import Topbar from '../components/Topbar'
import StatCard from '../components/StatCard'
import WorkflowMissionControl from '../components/WorkflowMissionControl'
import { useWorkflowStatus } from '../hooks/useWorkflowStatus'

export default function Dashboard({ status, trackerItems = [], onNavigate }) {
  const recentItems = trackerItems.slice(0, 3)
  const [filters, setFilters] = useState({ workflow_id: '', stage: '', severity: '', event_type: '', status: '', search: '', from_date: '', to_date: '', page: 1, limit: 8 })
  const { data, loading, refreshing, error, lastUpdated, refreshNow, connectionState } = useWorkflowStatus({ pollMs: 10000, transport: 'sse', filters })
  const overview = data.overview || { active: 0, completed: 0, failed: 0, queued: 0 }
  const analytics = data.analytics || {}
  const observability = data.observability || {}

  return (
    <div className="page page-wide">
      <Topbar
        title="AI Mission Control"
        subtitle="Monitor live resume intelligence workflows, AI activity, and automation readiness from one control surface."
        status={status}
      />

      <section className="hero-card">
        <div className="hero-grid">
          <div>
            <p className="eyebrow">AI Career Copilot</p>
            <h2>Operate live resume intelligence workflows like a compact mission control system.</h2>
            <p>
              Watch each workflow move from upload through parsing, scoring, and optimization readiness,
              with live SSE delivery now and multi-transport orchestration ready next.
            </p>
            <div className="hero-actions">
              <button type="button" className="btn-primary" onClick={() => onNavigate?.('start-apply')}>
                Launch Workflow
              </button>
              <button type="button" className="btn-ghost" onClick={() => onNavigate?.('tracker')}>
                Open Tracker
              </button>
            </div>
          </div>

          <div className="hero-aside panel-inset">
            <div className="hero-aside-header">
              <span className="section-kicker">AI activity</span>
              <span className={`status-pill ${status?.online ? 'online' : 'offline'}`}>{status?.label}</span>
            </div>
            <div className="activity-list">
              <div className="activity-item">
                <span className="activity-dot glow-cyan" />
                <div>
                  <strong>Live workflow states</strong>
                  <span>Queued, active, failed, and completed runs surface automatically.</span>
                </div>
              </div>
              <div className="activity-item">
                <span className="activity-dot glow-purple" />
                <div>
                  <strong>Execution telemetry</strong>
                  <span>Progress, duration, ATS score, and last activity stay visible.</span>
                </div>
              </div>
              <div className="activity-item">
                <span className="activity-dot glow-blue" />
                <div>
                  <strong>Automation ready</strong>
                  <span>Prepared for future websockets, queues, and n8n monitoring.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="Active workflows" value={overview.active} detail="Currently executing AI workflow stages." tone="cyan" />
        <StatCard label="Completed" value={overview.completed} detail="Optimization-ready workflows." tone="purple" />
        <StatCard label="Success rate" value={`${Math.round(analytics.workflow_success_rate || 0)}%`} detail="Filtered orchestration success across the current console view." tone="blue" />
        <StatCard label="Failed" value={overview.failed} detail="Runs needing manual attention or retry." tone="danger" />
      </section>

      <section className="stats-grid compact-stats-grid">
        <StatCard label="Avg execution" value={analytics.average_execution_seconds ? `${Math.round(analytics.average_execution_seconds)}s` : '--'} detail="Average workflow duration." tone="cyan" />
        <StatCard label="ATS average" value={analytics.ats_score_trends?.average ?? '--'} detail="Current ATS trend across filtered workflows." tone="purple" />
        <StatCard label="Queue depth" value={observability.orchestration_metrics?.queue_depth ?? 0} detail="Pending orchestration tasks in the local worker queue." tone="blue" />
        <StatCard label="Workers" value={observability.worker_metrics?.total_workers ?? 0} detail="Registered local workers and lease-aware execution readiness." tone="cyan" />
      </section>

      <section className="panel-card mission-control-panel">
        <WorkflowMissionControl
          data={data}
          loading={loading}
          refreshing={refreshing}
          error={error}
          lastUpdated={lastUpdated}
          connectionState={connectionState}
          onRefresh={refreshNow}
          filters={filters}
          onFiltersChange={setFilters}
        />
      </section>

      <section className="panel-grid two-column dashboard-bottom-grid">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Quick actions</span>
              <h3>Move faster</h3>
            </div>
          </div>
          <div className="quick-actions-grid">
            <button type="button" className="quick-action-card" onClick={() => onNavigate?.('start-apply')}>
              <strong>Start Apply</strong>
              <span>Begin a multi-step resume and target-role workflow.</span>
            </button>
            <button type="button" className="quick-action-card" onClick={() => onNavigate?.('resume')}>
              <strong>Review resume</strong>
              <span>Open AI suggestions tailored to your latest target role.</span>
            </button>
          </div>
        </div>

        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Recent applications</span>
              <h3>Latest application records</h3>
            </div>
          </div>
          {recentItems.length === 0 ? (
            <p className="muted-block">No applications yet. Your recent jobs will appear here.</p>
          ) : (
            <div className="recent-list">
              {recentItems.map((item, index) => (
                <div key={`${item.company}-${item.role}-${index}`} className="recent-item">
                  <div>
                    <strong>{item.company}</strong>
                    <span>{item.role}</span>
                  </div>
                  <span className={`tracker-badge status-${item.status}`}>{item.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
