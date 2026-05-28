import { API_BASE } from './api'

function buildStreamUrl(filters = {}) {
  const url = new URL(`${API_BASE}/workflow-status/stream`)
  Object.entries(filters).forEach(([key, value]) => {
    if (value) url.searchParams.set(key, value)
  })
  return url.toString()
}

export function createWorkflowTransport(mode = 'sse') {
  if (mode === 'websocket') {
    return {
      mode: 'websocket-ready',
      connect(_handlers, _filters = {}) {
        return () => {}
      },
    }
  }

  return {
    mode: 'sse',
    connect(handlers, filters = {}) {
      const source = new EventSource(buildStreamUrl(filters))

      source.onopen = () => {
        handlers.onOpen?.()
      }

      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          handlers.onEnvelope?.(payload)
        } catch {
          /* ignore malformed events */
        }
      }

      source.onerror = () => {
        handlers.onError?.('Workflow stream disconnected.')
      }

      return () => source.close()
    },
  }
}