import { useEffect, useState } from 'react'
import { getWorkflowStatus } from '../api/api'
import { useWorkflowStream } from './useWorkflowStream'

const DEFAULT_DATA = {
  profiles: [],
  activity_feed: [],
  overview: { active: 0, completed: 0, failed: 0, queued: 0, total: 0 },
  queue: { size: 0, pending: [] },
  automation_placeholders: {},
  transport: {},
  analytics: {},
  observability: {},
  event_query: { results: [], total: 0, filters: {}, page: 1, page_size: 8, pages: 1, aggregations: {} },
  active_filters: {},
}

export function useWorkflowStatus(options = 8000) {
  const config = typeof options === 'number' ? { pollMs: options, transport: 'sse', filters: {} } : { pollMs: 8000, transport: 'sse', filters: {}, ...(options || {}) }
  const pollMs = config.pollMs
  const filtersKey = JSON.stringify(config.filters || {})
  const stream = useWorkflowStream({ transport: config.transport, filters: config.filters })
  const [data, setData] = useState(DEFAULT_DATA)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function load(isBackground = false) {
      if (isBackground) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      try {
        const payload = await getWorkflowStatus(config.filters || {})
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
    } else {
      load(false)
      timer = window.setInterval(() => load(true), pollMs)
    }

    return () => {
      cancelled = true
      if (timer) window.clearInterval(timer)
    }
  }, [pollMs, reloadKey, config.transport, filtersKey])

  useEffect(() => {
    if (config.transport !== 'sse') return
    const envelope = stream.envelope
    if (!envelope) return
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
  }, [stream.envelope, config.transport])

  useEffect(() => {
    if (config.transport !== 'sse') return
    if (stream.error) setError(stream.error)
  }, [stream.error, config.transport])

  return {
    data,
    loading,
    refreshing,
    error,
    lastUpdated,
    transportMode: config.transport,
    connectionState: config.transport === 'sse' ? stream.connectionState : 'polling',
    refreshNow: () => setReloadKey((value) => value + 1),
  }
}