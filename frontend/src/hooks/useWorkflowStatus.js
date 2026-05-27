import { useEffect, useState } from 'react'
import { getWorkflowStatus, streamWorkflowStatus } from '../api/api'

const DEFAULT_DATA = {
  profiles: [],
  activity_feed: [],
  overview: { active: 0, completed: 0, failed: 0, queued: 0, total: 0 },
  queue: { size: 0, pending: [] },
  automation_placeholders: {},
  transport: {},
}

export function useWorkflowStatus(options = 8000) {
  const config = typeof options === 'number' ? { pollMs: options, transport: 'sse' } : { pollMs: 8000, transport: 'sse', ...(options || {}) }
  const pollMs = config.pollMs
  const [data, setData] = useState(DEFAULT_DATA)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    let stopStream = () => {}

    async function load(isBackground = false) {
      if (isBackground) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      try {
        const payload = await getWorkflowStatus()
        if (cancelled) return
        setData({ ...DEFAULT_DATA, ...payload })
        setLastUpdated(new Date().toISOString())
        setError('')
      } catch (err) {
        if (cancelled) return
        setError(err.response?.data?.detail || err.message || 'Failed to load workflows.')
      } finally {
        if (cancelled) return
        setLoading(false)
        setRefreshing(false)
      }
    }

    let timer = 0

    if (config.transport === 'sse') {
      load(false)
      stopStream = streamWorkflowStatus({
        onEnvelope: (envelope) => {
          if (cancelled) return
          if (envelope.type === 'heartbeat') {
            setLastUpdated(new Date().toISOString())
            return
          }
          const payload = envelope.payload || envelope
          setData({ ...DEFAULT_DATA, ...payload })
          setLastUpdated(new Date().toISOString())
          setLoading(false)
          setRefreshing(false)
          setError('')
        },
        onError: (message) => {
          if (cancelled) return
          setError(message || 'Workflow stream disconnected.')
        },
      })
    } else {
      load(false)
      timer = window.setInterval(() => load(true), pollMs)
    }

    return () => {
      cancelled = true
      if (timer) window.clearInterval(timer)
      stopStream()
    }
  }, [pollMs, reloadKey, config.transport])

  return {
    data,
    loading,
    refreshing,
    error,
    lastUpdated,
    transportMode: config.transport,
    refreshNow: () => setReloadKey((value) => value + 1),
  }
}