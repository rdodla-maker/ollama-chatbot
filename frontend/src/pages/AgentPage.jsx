import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar'
import ChatWindow from '../components/ChatWindow'
import AgentReasoning from '../components/AgentReasoning'
import ExecutionPlan from '../components/ExecutionPlan'
import ToolActivity from '../components/ToolActivity'
import { useAgent } from '../hooks/useAgent'
import { getPendingChanges, approveChange, rejectChange } from '../api/api'

export default function AgentPage({ status }) {
  const {
    messages,
    reasoning,
    plan,
    planSteps,
    toolActivity,
    loading,
    sendMessage,
    clearSession,
  } = useAgent({ stream: true })

  const [reasoningCollapsed, setReasoningCollapsed] = useState(false)
  const [planCollapsed, setPlanCollapsed] = useState(false)
  const [pending, setPending] = useState([])

  const loadPending = async () => {
    try {
      const data = await getPendingChanges()
      setPending(data)
    } catch {
      setPending([])
    }
  }

  useEffect(() => {
    if (!loading) loadPending()
  }, [loading, messages.length])

  const handleApprove = async (id) => {
    await approveChange(id)
    loadPending()
  }

  const handleReject = async (id) => {
    await rejectChange(id)
    loadPending()
  }

  return (
    <div className="page page-agent">
      <Topbar
        title="Autonomous Agent"
        subtitle="Tools · planning · memory · ReAct loop"
        status={status}
        onClear={clearSession}
        clearLabel="Clear session"
      />
      <div className="agent-layout">
        <div className="agent-main">
          <ChatWindow
            messages={messages}
            loading={loading}
            onSend={sendMessage}
            placeholder="Ask the agent to analyze code, search PDFs, run tools…"
            emptyTitle="Autonomous agent"
            emptyDescription="The agent can use tools, plan steps, and remember past tasks."
          />
        </div>
        <aside className="agent-side">
          <ExecutionPlan
            plan={plan}
            steps={planSteps}
            collapsed={planCollapsed}
            onToggle={() => setPlanCollapsed((c) => !c)}
          />
          <AgentReasoning
            steps={reasoning}
            collapsed={reasoningCollapsed}
            onToggle={() => setReasoningCollapsed((c) => !c)}
          />
          <ToolActivity tools={toolActivity} pending={pending} />
          {pending.length > 0 && (
            <div className="panel-card">
              <div className="panel-card-header">
                <h3>Approve edits</h3>
              </div>
              {pending.map((p) => (
                <div key={p.id} className="approval-row">
                  <code>{p.file_path}</code>
                  <div className="approval-actions">
                    <button type="button" className="btn-primary" onClick={() => handleApprove(p.id)}>
                      Approve
                    </button>
                    <button type="button" className="btn-ghost" onClick={() => handleReject(p.id)}>
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
