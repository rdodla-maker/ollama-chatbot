import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 180000,
})

export async function healthCheck() {
  const { data } = await api.get('/')
  return data
}

export async function sendChat(message) {
  const { data } = await api.post('/chat', { message })
  return data
}

export async function sendAgent(message) {
  const { data } = await api.post('/agent', { message })
  return data
}

export async function uploadPdf(file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload-pdf', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    },
  })
  return data
}

export async function indexCodebase() {
  const { data } = await api.post('/index-codebase')
  return data
}

/**
 * Stream chat tokens via SSE from POST /chat/stream
 */
export function streamChat(message, { onToken, onDone, onError }) {
  const url = `${API_BASE}/chat/stream`
  const controller = new AbortController()

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || err.error || response.statusText)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.error) {
              onError?.(payload.error)
              return
            }
            if (payload.token) onToken?.(payload.token)
            if (payload.done) onDone?.()
          } catch {
            /* ignore parse errors */
          }
        }
      }
      onDone?.()
    })
    .catch((err) => onError?.(err.message || 'Stream failed'))

  return () => controller.abort()
}

export async function fetchPendingChanges() {
  const { data } = await api.get('/pending-changes')
  return data
}

export async function approveChange(changeId) {
  const { data } = await api.post(`/pending-changes/${changeId}/approve`)
  return data
}

export async function rejectChange(changeId) {
  const { data } = await api.post(`/pending-changes/${changeId}/reject`)
  return data
}

/**
 * Stream agent events: plan, reasoning steps, tokens, done
 */
export function streamAgent(message, { onPlan, onReasoning, onToken, onDone, onError }) {
  const url = `${API_BASE}/agent/stream`
  const controller = new AbortController()

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || err.error || response.statusText)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'error' || payload.message) {
              onError?.(payload.message || payload.error || 'Agent error')
              return
            }
            if (payload.type === 'plan') onPlan?.(payload.content)
            if (payload.type === 'reasoning') onReasoning?.(payload.step)
            if (payload.type === 'token') onToken?.(payload.content)
            if (payload.type === 'done') onDone?.(payload)
          } catch {
            /* ignore */
          }
        }
      }
      onDone?.()
    })
    .catch((err) => onError?.(err.message || 'Stream failed'))

  return () => controller.abort()
}
