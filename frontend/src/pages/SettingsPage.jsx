import { useEffect, useState } from 'react'
import Topbar from '../components/Topbar'
import { getHealth } from '../api/api'

const STORAGE_KEY = 'local-ai-settings'

function loadSettings() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

export default function SettingsPage({ status, onThemeChange }) {
  const [settings, setSettings] = useState(() => ({
    streamChat: true,
    streamAgent: true,
    compactSidebar: false,
    ...loadSettings(),
  }))
  const [server, setServer] = useState(null)

  useEffect(() => {
    getHealth()
      .then(setServer)
      .catch(() => setServer(null))
  }, [])

  const update = (key, value) => {
    const next = { ...settings, [key]: value }
    setSettings(next)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    if (key === 'theme') onThemeChange?.(value)
  }

  return (
    <div className="page page-settings">
      <Topbar title="Settings" subtitle="Local preferences — no account required" status={status} />
      <div className="settings-grid">
        <section className="settings-card">
          <h3>Server (read-only)</h3>
          <dl className="settings-dl">
            <dt>Ollama URL</dt>
            <dd>{server?.ollama_url || '—'}</dd>
            <dt>Model</dt>
            <dd>{server?.model || '—'}</dd>
            <dt>Agent mode</dt>
            <dd>{server?.agent_mode || '—'}</dd>
            <dt>API</dt>
            <dd>{import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}</dd>
          </dl>
          <p className="panel-muted">Change model/URL in backend <code>.env</code></p>
        </section>

        <section className="settings-card">
          <h3>Preferences</h3>
          <label className="settings-row">
            <span>Stream chat responses</span>
            <input
              type="checkbox"
              checked={settings.streamChat !== false}
              onChange={(e) => update('streamChat', e.target.checked)}
            />
          </label>
          <label className="settings-row">
            <span>Stream agent responses</span>
            <input
              type="checkbox"
              checked={settings.streamAgent !== false}
              onChange={(e) => update('streamAgent', e.target.checked)}
            />
          </label>
          <label className="settings-row">
            <span>Compact sidebar</span>
            <input
              type="checkbox"
              checked={!!settings.compactSidebar}
              onChange={(e) => update('compactSidebar', e.target.checked)}
            />
          </label>
        </section>

        <section className="settings-card">
          <h3>About</h3>
          <p className="panel-muted">
            Personal local AI workspace — Ollama, RAG, LangGraph agent, ChromaDB.
            No auth. No cloud. Your machine.
          </p>
        </section>
      </div>
    </div>
  )
}
