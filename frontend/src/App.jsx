import { useEffect, useState } from 'react'
import AgentPanel from './components/AgentPanel'
import ChatPanel from './components/ChatPanel'
import PdfUpload from './components/PdfUpload'
import { healthCheck } from './api/client'
import './App.css'

const TABS = [
  { id: 'chat', label: 'PDF Chat' },
  { id: 'agent', label: 'Agent' },
  { id: 'upload', label: 'Upload' },
]

export default function App() {
  const [tab, setTab] = useState('chat')
  const [status, setStatus] = useState('connecting')

  useEffect(() => {
    healthCheck()
      .then((data) => setStatus(data.message || 'connected'))
      .catch(() => setStatus('backend offline'))
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Ollama Agentic AI</h1>
          <p className="subtitle">RAG · LangGraph Agent · Local LLM</p>
        </div>
        <span className={`status-badge status-${status.includes('offline') ? 'off' : 'on'}`}>
          {status}
        </span>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`tab ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="main">
        {tab === 'chat' && <ChatPanel />}
        {tab === 'agent' && <AgentPanel />}
        {tab === 'upload' && <PdfUpload />}
      </main>
    </div>
  )
}
