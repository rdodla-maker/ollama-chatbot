import { useEffect, useState } from 'react'
import WorkflowCard from './WorkflowCard'
import LiveWorkflowTimeline from './LiveWorkflowTimeline'
import WorkflowEventFeed from './WorkflowEventFeed'
import AutomationReadiness from './AutomationReadiness'
import { getResumeVersionDetail, performWorkflowAction, rollbackResumeVersion } from '../api/api'

function formatUpdated(value) {
  if (!value) return 'Awaiting first sync'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Awaiting first sync'
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const FILTER_OPTIONS = {
  stage: ['', 'processing', 'parsing_started', 'skills_extracted', 'ats_analysis', 'optimization_ready', 'paused', 'failed'],
  severity: ['', 'info', 'warning', 'error'],
  event_type: ['', 'workflow.paused', 'workflow.resumed', 'analysis.started', 'analysis.failed', 'optimization.completed', 'workflow.cancelled'],
  status: ['', 'queued', 'processing', 'retrying', 'paused', 'failed', 'analyzed', 'cancelled'],
}

export default function WorkflowMissionControl({ data, loading, refreshing, error, lastUpdated, connectionState, onRefresh, filters = {}, onFiltersChange }) {
  const profiles = data.profiles || []
  const [selectedId, setSelectedId] = useState('')
  const [actionState, setActionState] = useState({ workflowId: '', action: '', message: '', error: '' })
  const [versionState, setVersionState] = useState({ message: '', error: '', versionId: '' })
  const [selectedVersionId, setSelectedVersionId] = useState('')
  const [versionDetail, setVersionDetail] = useState(null)
  const [versionDetailError, setVersionDetailError] = useState('')
  const [versionDetailLoading, setVersionDetailLoading] = useState(false)

  useEffect(() => {
    if (!profiles.length) return
    setSelectedId((current) => {
      if (current && profiles.some((item) => item.id === current)) return current
      return profiles[0].id
    })
  }, [profiles])

  const selectedWorkflow = profiles.find((item) => item.id === selectedId) || profiles[0] || null
  const analytics = data.analytics || {}
  const observability = data.observability || {}
  const queryMeta = data.event_query || {}
  const queryResults = queryMeta.results || []
  const queryAggregations = queryMeta.aggregations || {}
  const feedItems = queryResults.length || Object.values(filters || {}).some(Boolean) ? queryResults : (data.activity_feed || [])
  const candidateProfile = selectedWorkflow?.candidate_profile || {}
  const candidateMemory = selectedWorkflow?.candidate_memory || []
  const resumeVersions = selectedWorkflow?.resume_versions || []
  const performance = analytics.performance || {}
  const failureDiagnostics = selectedWorkflow?.failure_diagnostics || {}
  const executionMetadata = selectedWorkflow?.execution_metadata || {}
  const queryPage = queryMeta.page || Number(filters.page) || 1
  const totalPages = queryMeta.pages || 1

  useEffect(() => {
    if (!resumeVersions.length) {
      setSelectedVersionId('')
      setVersionDetail(null)
      return
    }
    setSelectedVersionId((current) => {
      if (current && resumeVersions.some((item) => item.id === current)) return current
      return resumeVersions.find((item) => item.is_active)?.id || resumeVersions[0].id
    })
  }, [resumeVersions])

  useEffect(() => {
    let cancelled = false

    async function loadVersionDetail() {
      if (!selectedVersionId) {
        setVersionDetail(null)
        setVersionDetailError('')
        return
      }
      setVersionDetailLoading(true)
      setVersionDetailError('')
      try {
        const payload = await getResumeVersionDetail(selectedVersionId)
        if (cancelled) return
        setVersionDetail(payload)
      } catch (err) {
        if (cancelled) return
        setVersionDetail(null)
        setVersionDetailError(err.response?.data?.detail || err.message || 'Unable to load version comparison.')
      } finally {
        if (!cancelled) setVersionDetailLoading(false)
      }
    }

    loadVersionDetail()
    return () => {
      cancelled = true
    }
  }, [selectedVersionId])

  async function handleAction(workflowId, action, stage) {
    setActionState({ workflowId, action: `${action}:${stage || ''}`, message: '', error: '' })
    try {
      const result = await performWorkflowAction(workflowId, action, stage)
      setActionState({ workflowId: '', action: '', message: result.message, error: '' })
      onRefresh?.()
    } catch (err) {
      setActionState({
        workflowId: '',
        action: '',
        message: '',
        error: err.response?.data?.detail || err.message || 'Workflow action failed.',
      })
    }
  }

  async function handleRollback(versionId) {
    setVersionState({ versionId, message: '', error: '' })
    try {
      const result = await rollbackResumeVersion(versionId)
      setVersionState({ versionId: '', message: `${result.version_label} restored.`, error: '' })
      setSelectedVersionId(versionId)
      onRefresh?.()
    } catch (err) {
      setVersionState({ versionId: '', message: '', error: err.response?.data?.detail || err.message || 'Resume rollback failed.' })
    }
  }

  function updateFilter(key, value) {
    const nextValue = key === 'page' || key === 'limit' ? Number(value) || 1 : value
    onFiltersChange?.({ ...filters, [key]: nextValue, ...(key === 'page' ? {} : { page: 1 }) })
  }

  function clearFilters() {
    onFiltersChange?.({ workflow_id: '', stage: '', severity: '', event_type: '', status: '', search: '', from_date: '', to_date: '', page: 1, limit: filters.limit || 8 })
  }

  return (
    <div className="mission-control-stack">
      <div className="mission-control-header">
        <div>
          <span className="section-kicker">AI Mission Control</span>
          <h3>Live workflow operating view</h3>
          <p className="muted-block">SSE-backed live operations now, websocket-ready next.</p>
        </div>
        <div className="pill-stack">
          <span className={`soft-pill ${refreshing ? 'accent' : ''}`}>{refreshing ? 'Refreshing' : 'Live SSE stream'}</span>
          <span className={`soft-pill connection-${connectionState || 'connecting'}`}>Stream {connectionState || 'connecting'}</span>
          <span className="soft-pill">Updated {formatUpdated(lastUpdated)}</span>
        </div>
      </div>

      {loading ? <p className="muted-block">Loading workflows...</p> : null}
      {error ? <p className="form-error">{error}</p> : null}
      {actionState.message ? <p className="form-success">{actionState.message}</p> : null}
      {actionState.error ? <p className="form-error">{actionState.error}</p> : null}
      {versionState.message ? <p className="form-success">{versionState.message}</p> : null}
      {versionState.error ? <p className="form-error">{versionState.error}</p> : null}
      {!loading && !profiles.length ? <p className="muted-block">No workflows yet. Upload a resume to start the first orchestration run.</p> : null}

      <div className="panel-inset mission-filter-bar">
        <div className="panel-card-header compact mission-filter-head">
          <div>
            <span className="section-kicker">Operational filters</span>
            <h4>Filter live workflows and orchestration events</h4>
          </div>
          <button type="button" className="btn-ghost small-btn" onClick={clearFilters}>Clear filters</button>
        </div>
        <div className="mission-filter-grid">
          <label className="field compact-field">
            <span>Workflow ID</span>
            <input value={filters.workflow_id || ''} onChange={(event) => updateFilter('workflow_id', event.target.value)} placeholder="wf-1234" />
          </label>
          <label className="field compact-field">
            <span>Stage</span>
            <select value={filters.stage || ''} onChange={(event) => updateFilter('stage', event.target.value)}>
              {FILTER_OPTIONS.stage.map((value) => <option key={value || 'all-stage'} value={value}>{value || 'All stages'}</option>)}
            </select>
          </label>
          <label className="field compact-field">
            <span>Severity</span>
            <select value={filters.severity || ''} onChange={(event) => updateFilter('severity', event.target.value)}>
              {FILTER_OPTIONS.severity.map((value) => <option key={value || 'all-severity'} value={value}>{value || 'All severities'}</option>)}
            </select>
          </label>
          <label className="field compact-field">
            <span>Event type</span>
            <select value={filters.event_type || ''} onChange={(event) => updateFilter('event_type', event.target.value)}>
              {FILTER_OPTIONS.event_type.map((value) => <option key={value || 'all-event'} value={value}>{value || 'All events'}</option>)}
            </select>
          </label>
          <label className="field compact-field">
            <span>Status</span>
            <select value={filters.status || ''} onChange={(event) => updateFilter('status', event.target.value)}>
              {FILTER_OPTIONS.status.map((value) => <option key={value || 'all-status'} value={value}>{value || 'All statuses'}</option>)}
            </select>
          </label>
          <label className="field compact-field search-field">
            <span>Event search</span>
            <input value={filters.search || ''} onChange={(event) => updateFilter('search', event.target.value)} placeholder="timeout, ATS, paused" />
          </label>
          <label className="field compact-field">
            <span>From</span>
            <input type="datetime-local" value={filters.from_date || ''} onChange={(event) => updateFilter('from_date', event.target.value)} />
          </label>
          <label className="field compact-field">
            <span>To</span>
            <input type="datetime-local" value={filters.to_date || ''} onChange={(event) => updateFilter('to_date', event.target.value)} />
          </label>
          <label className="field compact-field">
            <span>Page size</span>
            <select value={filters.limit || 8} onChange={(event) => updateFilter('limit', event.target.value)}>
              {[8, 12, 20].map((value) => <option key={value} value={value}>{value} events</option>)}
            </select>
          </label>
        </div>
      </div>

      <div className="panel-grid analytics-grid">
        <div className="panel-inset mission-detail-card analytics-card">
          <div className="panel-card-header compact">
            <div>
              <span className="section-kicker">Workflow analytics</span>
              <h4>Execution intelligence</h4>
            </div>
          </div>
          <div className="mission-summary-grid">
            <div>
              <span className="workflow-stat-label">Success rate</span>
              <strong>{Math.round(analytics.workflow_success_rate || 0)}%</strong>
            </div>
            <div>
              <span className="workflow-stat-label">Avg execution</span>
              <strong>{analytics.average_execution_seconds ? `${Math.round(analytics.average_execution_seconds)}s` : '--'}</strong>
            </div>
            <div>
              <span className="workflow-stat-label">Retry volume</span>
              <strong>{analytics.retry_statistics?.total_retries ?? 0}</strong>
            </div>
            <div>
              <span className="workflow-stat-label">ATS average</span>
              <strong>{analytics.ats_score_trends?.average ?? '--'}</strong>
            </div>
          </div>
          <div className="mini-list">
            {(analytics.stage_bottlenecks || []).slice(0, 3).map((item) => (
              <div key={item.stage} className="mini-list-item">
                <strong>{item.stage.replaceAll('_', ' ')}</strong>
                <span>{item.average_duration_seconds}s avg · {item.samples} samples</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel-inset mission-detail-card analytics-card">
          <div className="panel-card-header compact">
            <div>
              <span className="section-kicker">Observability</span>
              <h4>Operational visibility</h4>
            </div>
          </div>
          <div className="mission-summary-grid">
            <div>
              <span className="workflow-stat-label">Workers</span>
              <strong>{observability.worker_metrics?.total_workers ?? 0}</strong>
            </div>
            <div>
              <span className="workflow-stat-label">Active leases</span>
              <strong>{observability.orchestration_metrics?.active_leases ?? 0}</strong>
            </div>
            <div>
              <span className="workflow-stat-label">Queue depth</span>
              <strong>{observability.orchestration_metrics?.queue_depth ?? 0}</strong>
            </div>
            <div>
              <span className="workflow-stat-label">Failures</span>
              <strong>{observability.failure_analytics?.total_failures ?? 0}</strong>
            </div>
          </div>
          <div className="mini-list">
            {(observability.failure_analytics?.top_reasons || []).slice(0, 3).map((item) => (
              <div key={item.reason} className="mini-list-item">
                <strong>{item.reason}</strong>
                <span>{item.count} occurrences</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {profiles.length ? (
        <div className="mission-grid">
          <div className="workflow-card-grid">
            {profiles.map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                workflow={workflow}
                selected={workflow.id === selectedWorkflow?.id}
                onSelect={setSelectedId}
                onAction={handleAction}
                actionLoading={actionState.workflowId === workflow.id && Boolean(actionState.action)}
              />
            ))}
          </div>

          <div className="mission-detail-stack">
            <div className="panel-inset mission-detail-card">
              <div className="panel-card-header compact">
                <div>
                  <span className="section-kicker">Execution summary</span>
                  <h4>{selectedWorkflow?.execution_summary || 'Workflow summary pending'}</h4>
                </div>
                <span className={`mission-badge tone-${selectedWorkflow?.current_stage_state || 'queued'}`}>
                  {selectedWorkflow?.current_stage_state || 'queued'}
                </span>
              </div>
              <div className="mission-summary-grid">
                <div>
                  <span className="workflow-stat-label">Current stage</span>
                  <strong>{selectedWorkflow?.current_stage_label}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Queued actions</span>
                  <strong>{selectedWorkflow?.queued_actions?.length || 0}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Workflow duration</span>
                  <strong>{selectedWorkflow?.workflow_duration_seconds != null ? `${Math.round(selectedWorkflow.workflow_duration_seconds)}s` : 'Live'}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">ATS score</span>
                  <strong>{selectedWorkflow?.ats_score ?? '--'}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Retry count</span>
                  <strong>{selectedWorkflow?.retry_count || 0}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Failure reason</span>
                  <strong>{selectedWorkflow?.failure_reason || 'None'}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Worker owner</span>
                  <strong>{executionMetadata.worker_owner || '--'}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Recovery state</span>
                  <strong>{executionMetadata.recovery_state || 'stable'}</strong>
                </div>
              </div>
              {(selectedWorkflow?.stage_actions || []).length ? (
                <div className="stage-action-group">
                  <span className="workflow-stat-label">Stage-level recovery</span>
                  <div className="workflow-action-row compact">
                    {selectedWorkflow.stage_actions.map((item) => (
                      <button
                        key={`${item.action}-${item.stage}`}
                        type="button"
                        className={`workflow-action-btn ${item.enabled ? '' : 'disabled'}`}
                        disabled={!item.enabled || (actionState.workflowId === selectedWorkflow.id && Boolean(actionState.action))}
                        title={item.reason || item.label}
                        onClick={() => handleAction(selectedWorkflow.id, item.action, item.stage)}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
              {(executionMetadata.recovery_actions || []).length ? (
                <div className="stage-action-group">
                  <span className="workflow-stat-label">Workflow recovery controls</span>
                  <div className="workflow-action-row compact">
                    {executionMetadata.recovery_actions.map((item) => (
                      <button
                        key={`${item.action}-${item.stage || 'workflow'}`}
                        type="button"
                        className={`workflow-action-btn ${item.enabled ? '' : 'disabled'}`}
                        disabled={!item.enabled || (actionState.workflowId === selectedWorkflow.id && Boolean(actionState.action))}
                        title={item.reason || item.label}
                        onClick={() => handleAction(selectedWorkflow.id, item.action, item.stage)}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="panel-inset mission-detail-card">
              <div className="panel-card-header compact">
                <div>
                  <span className="section-kicker">Workflow timeline</span>
                  <h4>Execution stages</h4>
                </div>
              </div>
              <LiveWorkflowTimeline timeline={selectedWorkflow?.timeline || []} />
            </div>

            <div className="panel-inset mission-detail-card">
              <div className="panel-card-header compact">
                <div>
                  <span className="section-kicker">Failure diagnostics</span>
                  <h4>Recovery trace and suggestions</h4>
                </div>
              </div>
              {!failureDiagnostics.failure_reason ? (
                <p className="muted-block">No active failure diagnostics for this workflow.</p>
              ) : (
                <div className="diagnostic-stack">
                  <div className="mission-summary-grid">
                    <div>
                      <span className="workflow-stat-label">Failed stage</span>
                      <strong>{failureDiagnostics.failed_stage || '--'}</strong>
                    </div>
                    <div>
                      <span className="workflow-stat-label">Reason</span>
                      <strong>{failureDiagnostics.failure_reason || '--'}</strong>
                    </div>
                  </div>
                  <div className="mini-list">
                    {(failureDiagnostics.recovery_suggestions || []).map((item) => (
                      <div key={item} className="mini-list-item vertical-item">
                        <strong>Suggested next step</strong>
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                  <div className="trace-list">
                    {(failureDiagnostics.execution_trace || []).map((item, index) => (
                      <div key={`${item.timestamp || index}-${item.event_type || item.stage}`} className="trace-row">
                        <strong>{item.event_type || item.stage || 'workflow.event'}</strong>
                        <span>{formatDateTime(item.timestamp)} · {item.state || '--'} · {item.worker_owner || 'workflow-engine'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="panel-inset mission-detail-card">
              <div className="panel-card-header compact">
                <div>
                  <span className="section-kicker">Candidate intelligence</span>
                  <h4>{candidateProfile.display_name || 'Candidate memory pending'}</h4>
                </div>
              </div>
              <div className="mission-summary-grid">
                <div>
                  <span className="workflow-stat-label">Preferred roles</span>
                  <strong>{(candidateProfile.preferred_roles || []).slice(0, 2).join(', ') || '--'}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Top skills</span>
                  <strong>{(candidateProfile.skills || []).slice(0, 2).join(', ') || '--'}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">Strengths</span>
                  <strong>{(candidateProfile.strengths || []).slice(0, 2).join(', ') || '--'}</strong>
                </div>
                <div>
                  <span className="workflow-stat-label">ATS gaps</span>
                  <strong>{(candidateProfile.weaknesses || []).slice(0, 2).join(', ') || '--'}</strong>
                </div>
              </div>
              <div className="mini-list">
                {candidateMemory.slice(0, 4).map((item) => (
                  <div key={item.id} className="mini-list-item">
                    <strong>{item.memory_type.replaceAll('_', ' ')}</strong>
                    <span>{Object.values(item.content || {}).flat().slice(0, 2).join(', ') || 'Operational memory stored'}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div className="panel-grid two-column mission-bottom-grid">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Operational query</span>
              <h3>Event history explorer</h3>
            </div>
            <span className="soft-pill">{queryMeta.total || 0} matching events</span>
          </div>
          <div className="query-summary-grid">
            <div className="panel-inset query-summary-card">
              <span className="workflow-stat-label">Stage clusters</span>
              <div className="chip-list">
                {(queryAggregations.stage || []).slice(0, 4).map((item) => <span key={item.key} className="summary-chip">{item.key} · {item.count}</span>)}
              </div>
            </div>
            <div className="panel-inset query-summary-card">
              <span className="workflow-stat-label">Severity mix</span>
              <div className="chip-list">
                {(queryAggregations.severity || []).slice(0, 4).map((item) => <span key={item.key} className="summary-chip">{item.key} · {item.count}</span>)}
              </div>
            </div>
          </div>
          <WorkflowEventFeed activity={feedItems} />
          <div className="pagination-row">
            <button type="button" className="btn-ghost small-btn" onClick={() => updateFilter('page', Math.max(queryPage - 1, 1))} disabled={queryPage <= 1}>Previous</button>
            <span className="workflow-stat-label">Page {queryPage} of {totalPages}</span>
            <button type="button" className="btn-ghost small-btn" onClick={() => updateFilter('page', Math.min(queryPage + 1, totalPages))} disabled={queryPage >= totalPages}>Next</button>
          </div>
        </div>

        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Resume intelligence</span>
              <h3>Version history, diff, and rollback</h3>
            </div>
          </div>
          {!resumeVersions.length ? (
            <p className="muted-block">Resume versions will appear after uploads and optimization snapshots.</p>
          ) : (
            <div className="resume-version-layout">
              <div className="mini-list">
                {resumeVersions.map((item) => (
                  <div key={item.id} className={`version-row ${selectedVersionId === item.id ? 'selected-row' : ''}`}>
                    <button type="button" className="version-select-btn" onClick={() => setSelectedVersionId(item.id)}>
                      <strong>{item.version_label}</strong>
                      <span>{item.version_kind} · ATS {item.ats_score ?? '--'} · {item.diff_summary}</span>
                    </button>
                    <button
                      type="button"
                      className={`workflow-action-btn ${item.is_active ? 'disabled' : ''}`}
                      disabled={item.is_active || versionState.versionId === item.id}
                      onClick={() => handleRollback(item.id)}
                    >
                      {item.is_active ? 'Active' : versionState.versionId === item.id ? 'Restoring...' : 'Rollback'}
                    </button>
                  </div>
                ))}
              </div>

              <div className="panel-inset version-detail-card">
                <div className="panel-card-header compact">
                  <div>
                    <span className="section-kicker">Rollback preview</span>
                    <h4>{versionDetail?.version_label || 'Version comparison'}</h4>
                  </div>
                  <span className="soft-pill">ATS delta {versionDetail?.comparison?.ats_delta ?? '--'}</span>
                </div>
                {versionDetailLoading ? <p className="muted-block">Loading version comparison...</p> : null}
                {versionDetailError ? <p className="form-error">{versionDetailError}</p> : null}
                {versionDetail ? (
                  <div className="version-detail-stack">
                    <div className="mission-summary-grid">
                      <div>
                        <span className="workflow-stat-label">Current version</span>
                        <strong>{versionDetail.version_label}</strong>
                      </div>
                      <div>
                        <span className="workflow-stat-label">Previous version</span>
                        <strong>{versionDetail.previous_version?.version_label || 'None'}</strong>
                      </div>
                    </div>
                    <div className="diff-summary-grid">
                      <div className="panel-inset diff-summary-card">
                        <span className="workflow-stat-label">Added lines</span>
                        <div className="chip-list">
                          {(versionDetail.comparison?.added_lines || []).slice(0, 8).map((item) => <span key={`add-${item}`} className="summary-chip positive">{item}</span>)}
                        </div>
                      </div>
                      <div className="panel-inset diff-summary-card">
                        <span className="workflow-stat-label">Removed lines</span>
                        <div className="chip-list">
                          {(versionDetail.comparison?.removed_lines || []).slice(0, 8).map((item) => <span key={`remove-${item}`} className="summary-chip danger-chip">{item}</span>)}
                        </div>
                      </div>
                    </div>
                    <div className="diff-columns">
                      <div>
                        <span className="workflow-stat-label">Previous snapshot</span>
                        <pre className="diff-preview">{versionDetail.comparison?.previous_text || 'No previous snapshot.'}</pre>
                      </div>
                      <div>
                        <span className="workflow-stat-label">Current snapshot</span>
                        <pre className="diff-preview">{versionDetail.comparison?.current_text || 'No current snapshot.'}</pre>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="panel-grid analytics-grid">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Performance drill-down</span>
              <h3>Execution hotspots</h3>
            </div>
          </div>
          <div className="mini-list">
            {(performance.average_stage_duration || []).slice(0, 4).map((item) => (
              <div key={item.stage} className="mini-list-item">
                <strong>{item.stage.replaceAll('_', ' ')}</strong>
                <span>{item.average_duration_seconds}s avg · {item.samples} samples</span>
              </div>
            ))}
            {(performance.failure_hotspots || []).slice(0, 3).map((item) => (
              <div key={`failure-${item.stage}`} className="mini-list-item">
                <strong>{item.stage.replaceAll('_', ' ')}</strong>
                <span>{item.count} failure events</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Workflow audit</span>
              <h3>Ownership and control actions</h3>
            </div>
          </div>
          <div className="mini-list">
            {(observability.workflow_audit?.workflow_ownership || []).slice(0, 4).map((item) => (
              <div key={`owner-${item.owner}`} className="mini-list-item">
                <strong>{item.owner}</strong>
                <span>{item.count} owned workflow events</span>
              </div>
            ))}
            {(observability.execution_logs?.action_audit || []).slice(0, 3).map((item, index) => (
              <div key={`${item.timestamp || index}-${item.action}`} className="mini-list-item vertical-item">
                <strong>{item.action}</strong>
                <span>{item.owner || 'workflow-engine'} · {item.stage || 'workflow'} · {formatDateTime(item.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel-card">
        <div className="panel-card-header">
          <div>
            <span className="section-kicker">Automation readiness</span>
            <h3>Control plane placeholders</h3>
          </div>
        </div>
        <AutomationReadiness placeholders={data.automation_placeholders || {}} queue={data.queue} transport={data.transport} />
      </div>
    </div>
  )
}