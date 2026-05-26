import { useCallback, useRef, useState } from 'react'
import { postChat, streamChat } from '../api/api'

export function useChat({ stream = true } = {}) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const clearChat = useCallback(() => {
    abortRef.current?.()
    setMessages([])
    setError(null)
  }, [])

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text?.trim()
      if (!trimmed || loading) return

      setError(null)
      setLoading(true)
      setMessages((prev) => [...prev, { role: 'user', content: trimmed, id: Date.now() }])

      if (stream) {
        let aiText = ''
        const assistantId = Date.now() + 1
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '', id: assistantId, streaming: true },
        ])

        abortRef.current = streamChat(trimmed, {
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
        const data = await postChat(trimmed)
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: data.response,
            id: Date.now() + 1,
            sources: data.sources,
          },
        ])
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Chat failed')
      } finally {
        setLoading(false)
      }
    },
    [loading, stream]
  )

  return { messages, loading, error, sendMessage, clearChat, setError }
}
