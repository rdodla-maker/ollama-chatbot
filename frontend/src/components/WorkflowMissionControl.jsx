import { useEffect, useState } from 'react'
import WorkflowCard from './WorkflowCard'
import WorkflowTimeline from './WorkflowTimeline'
import AIActivityFeed from './AIActivityFeed'
import AutomationReadiness from './AutomationReadiness'
import { performWorkflowAction } from '../api/api'

function formatUpdated(value) {
  if (!value) return 'Awaiting first sync'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Awaiting first sync'
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function WorkflowMissionControl({ data, loading, refreshing, error, lastUpdated, onRefresh }) {
  const profiles = data.profiles || []
  const [selectedId, setSelectedId] = useState('')
  const [actionState, setActionState] = useState({ workflowId: '', action: '', message: '', error: '' })

  useEffect(() => {
    if (!profiles.length) return
    setSelectedId((current) => {
      if (current && profiles.some((item) => item.id === current)) return current
      return profiles[0].id
    })
  }, [profiles])

  const selectedWorkflow = profiles.find((item) => item.id === selectedId) || profiles[0] || null

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
          <span className="soft-pill">Updated {formatUpdated(lastUpdated)}</span>
        </div>
      </div>

      {loading ? <p className="muted-block">Loading workflows...</p> : null}
      {error ? <p className="form-error">{error}</p> : null}
      {actionState.message ? <p className="form-success">{actionState.message}</p> : null}
      {actionState.error ? <p className="form-error">{actionState.error}</p> : null}
      {!loading && !profiles.length ? <p className="muted-block">No workflows yet. Upload a resume to start the first orchestration run.</p> : null}

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
            </div>

            <div className="panel-inset mission-detail-card">
              <div className="panel-card-header compact">
                <div>
                  <span className="section-kicker">Workflow timeline</span>
                  <h4>Execution stages</h4>
                </div>
              </div>
              <WorkflowTimeline timeline={selectedWorkflow?.timeline || []} />
            </div>
          </div>
        </div>
      ) : null}

      <div className="panel-grid two-column mission-bottom-grid">
        <div className="panel-card">
          <div className="panel-card-header">
            <div>
              <span className="section-kicker">Recent AI activity</span>
              <h3>Event feed</h3>
            </div>
          </div>
          <AIActivityFeed activity={data.activity_feed || []} />
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
    </div>
  )
}