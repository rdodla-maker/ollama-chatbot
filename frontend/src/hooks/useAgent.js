import { useCallback, useRef, useState } from 'react'
import { postAgent, streamAgent } from '../api/api'

function parseToolsFromReasoning(steps) {
  return steps
    .filter((s) => s.startsWith('Action:'))
    .map((s) => {
      const match = s.match(/Action:\s*(\w+)\((.*)\)/)
      return {
        name: match?.[1] || 'tool',
        args: match?.[2] || '',
        raw: s,
      }
    })
}

function parsePlanSteps(planText) {
  if (!planText) return []
  return planText
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => /^\d+[\.\)]/.test(line) || line.startsWith('-'))
}

export function useAgent({ stream = true } = {}) {
  const [messages, setMessages] = useState([])
  const [reasoning, setReasoning] = useState([])
  const [plan, setPlan] = useState('')
  const [toolActivity, setToolActivity] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const clearSession = useCallback(() => {
    abortRef.current?.()
    setMessages([])
    setReasoning([])
    setPlan('')
    setToolActivity([])
    setError(null)
  }, [])

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text?.trim()
      if (!trimmed || loading) return

      setError(null)
      setLoading(true)
      setReasoning([])
      setToolActivity([])
      setMessages((prev) => [...prev, { role: 'user', content: trimmed, id: Date.now() }])

      if (stream) {
        let aiText = ''
        const steps = []
        const assistantId = Date.now() + 1
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '', id: assistantId, streaming: true },
        ])

        abortRef.current = streamAgent(trimmed, {
          onPlan: (p) => setPlan(p),
          onReasoning: (step) => {
            steps.push(step)
            setReasoning([...steps])
            setToolActivity(parseToolsFromReasoning(steps))
          },
          onToken: (token) => {
            aiText += token
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: aiText, streaming: true }
                  : m
              )
            )
          },
          onDone: () => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, streaming: false } : m
              )
            )
            setLoading(false)
          },
          onError: (msg) => {
            setError(msg)
            setLoading(false)
          },
        })
        return
      }

      try {
        const data = await postAgent(trimmed)
        setPlan(data.plan || '')
        const steps = data.reasoning || []
        setReasoning(steps)
        setToolActivity(parseToolsFromReasoning(steps))
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: data.response, id: Date.now() + 1 },
        ])
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Agent failed')
      } finally {
        setLoading(false)
      }
    },
    [loading, stream]
  )

  return {
    messages,
    reasoning,
    plan,
    planSteps: parsePlanSteps(plan),
    toolActivity,
    loading,
    error,
    sendMessage,
    clearSession,
    setError,
  }
}
