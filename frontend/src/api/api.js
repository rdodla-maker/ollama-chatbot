import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 180000,
})

export async function getHealth() {
  const { data } = await api.get('/')
  return data
}

export async function postChat(message) {
  const { data } = await api.post('/chat', { message })
  return data
}

export async function postAgent(message) {
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

export async function getMemory() {
  const { data } = await api.get('/memory')
  return data
}

export async function getPendingChanges() {
  const { data } = await api.get('/pending-changes')
  return data
}

export async function approveChange(id) {
  const { data } = await api.post(`/pending-changes/${id}/approve`)
  return data
}

export async function rejectChange(id) {
  const { data } = await api.post(`/pending-changes/${id}/reject`)
  return data
}

function parseSseLines(buffer, line, handlers) {
  if (!line.startsWith('data: ')) return buffer
  try {
    const payload = JSON.parse(line.slice(6))
    handlers(payload)
  } catch {
    /* ignore */
  }
  return buffer
}

export function streamChat(message, handlers) {
  const url = `${API_BASE}/chat/stream`
  const controller = new AbortController()
  const { onToken, onDone, onError } = handlers

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
            const p = JSON.parse(line.slice(6))
            if (p.error) {
              onError?.(p.error)
              return
            }
            if (p.token) onToken?.(p.token)
            if (p.done) onDone?.()
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

export function streamAgent(message, handlers) {
  const url = `${API_BASE}/agent/stream`
  const controller = new AbortController()
  const { onPlan, onReasoning, onToken, onDone, onError } = handlers

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
            const p = JSON.parse(line.slice(6))
            if (p.type === 'error' || (p.message && !p.type)) {
              onError?.(p.message || p.error || 'Agent error')
              return
            }
            if (p.type === 'plan') onPlan?.(p.content)
            if (p.type === 'reasoning') onReasoning?.(p.step)
            if (p.type === 'token') onToken?.(p.content)
            if (p.type === 'done') onDone?.(p)
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
