import { useState } from 'react'

const INITIAL_FORM = {
  company: '',
  role: '',
  job_description: '',
  skills: '',
  resume_text: '',
  tone: 'professional',
}

export default function JobApplicationForm({ onSubmit, loading, error }) {
  const [form, setForm] = useState(INITIAL_FORM)
  const [success, setSuccess] = useState('')

  const updateField = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSuccess('')
    try {
      await onSubmit(form)
      setSuccess('Application materials generated successfully.')
    } catch {
      // parent owns the error message
    }
  }

  return (
    <form className="panel-card form-card" onSubmit={handleSubmit}>
      <div className="panel-card-header">
        <div>
          <span className="section-kicker">AI generation</span>
          <h3>Job application form</h3>
          <p>Generate a personalized email, cover letter, and resume suggestions.</p>
        </div>
        <div className="pill-stack">
          <span className="soft-pill">Resume aware</span>
          <span className="soft-pill">Role tailored</span>
        </div>
      </div>

      {loading ? (
        <div className="ai-processing-bar" aria-hidden="true">
          <span />
        </div>
      ) : null}

      <div className="form-grid">
        <label className="field">
          <span>Company name</span>
          <input name="company" value={form.company} onChange={updateField} placeholder="Acme Inc." required />
        </label>

        <label className="field">
          <span>Role</span>
          <input name="role" value={form.role} onChange={updateField} placeholder="Frontend Engineer" required />
        </label>

        <label className="field field-full">
          <span>Skills</span>
          <input name="skills" value={form.skills} onChange={updateField} placeholder="React, FastAPI, Python, UX" required />
        </label>

        <label className="field">
          <span>Email tone</span>
          <select name="tone" value={form.tone} onChange={updateField}>
            <option value="professional">Professional</option>
            <option value="confident">Confident</option>
            <option value="friendly">Friendly</option>
          </select>
        </label>

        <label className="field field-full">
          <span>Job description</span>
          <textarea name="job_description" value={form.job_description} onChange={updateField} rows={8} placeholder="Paste the job description here..." required />
        </label>

        <label className="field field-full">
          <span>Resume text</span>
          <textarea name="resume_text" value={form.resume_text} onChange={updateField} rows={8} placeholder="Paste your current resume text here..." required />
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Generating...' : 'Generate Application Pack'}
        </button>
        <span className="form-hint">Ollama will generate three polished assets in one pass.</span>
        {success ? <span className="form-success">{success}</span> : null}
        {error ? <span className="form-error">{error}</span> : null}
      </div>
    </form>
  )
}