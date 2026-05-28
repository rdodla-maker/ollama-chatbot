import { useEffect, useState } from 'react'
import { createWorkflowTransport } from '../api/workflowTransport'

export function useWorkflowStream({ transport = 'sse', filters = {} } = {}) {
  const [connectionState, setConnectionState] = useState(transport === 'sse' ? 'connecting' : 'idle')
  const [envelope, setEnvelope] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const adapter = createWorkflowTransport(transport)
    const disconnect = adapter.connect(
      {
        onOpen: () => {
          setConnectionState('connected')
          setError('')
        },
        onEnvelope: (payload) => {
          setEnvelope(payload)
          if (payload?.type === 'heartbeat') return
          setConnectionState('connected')
          setError('')
        },
        onError: (message) => {
          setConnectionState('reconnecting')
          setError(message || 'Workflow stream disconnected.')
        },
      },
      filters,
    )

    return () => disconnect()
  }, [transport, JSON.stringify(filters)])

  return {
    envelope,
    connectionState,
    error,
  }
}