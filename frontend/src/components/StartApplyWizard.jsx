import { useState } from 'react'
import { uploadResume as apiUploadResume, analyzeResume as apiAnalyzeResume, getWorkflowStatus as apiWorkflowStatus } from '../api/api'

export default function StartApplyWizard({ onDone }) {
  const [step, setStep] = useState(1)
  const [file, setFile] = useState(null)
  const [uploadId, setUploadId] = useState(null)
  const [parsedSnippet, setParsedSnippet] = useState('')
  const [roles, setRoles] = useState([])
  const [roleInput, setRoleInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)

  function onFileChange(e) {
    const f = e.target.files?.[0]
    if (f) setFile(f)
  }

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    try {
      const res = await apiUploadResume(file, (p) => {})
      setUploadId(res.upload_id)
      setParsedSnippet(res.parsed_snippet || '')
      setStep(2)
    } catch (err) {
      alert(err?.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  function addRole() {
    const val = roleInput.trim()
    if (!val) return
    if (roles.includes(val)) {
      setRoleInput('')
      return
    }
    if (roles.length >= 5) {
      alert('Maximum of 5 roles allowed')
      return
    }
    setRoles((r) => [...r, val])
    setRoleInput('')
  }

  function removeRole(idx) {
    setRoles((r) => r.filter((_, i) => i !== idx))
  }

  async function handleAnalyze() {
    setLoading(true)
    try {
      const payload = { upload_id: uploadId, target_roles: roles }
      const res = await apiAnalyzeResume(payload)
      setAnalysis(res)
      setStep(4)
      // notify done
      onDone?.()
    } catch (err) {
      alert(err?.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="start-apply-wizard">
      <div className="wizard-step-indicator">Step {step} of 3</div>

      {step === 1 && (
        <div className="wizard-panel">
          <h3>Upload your resume (PDF or DOCX)</h3>
          <input type="file" accept=".pdf,.doc,.docx" onChange={onFileChange} />
          {file && <p className="muted-block">Selected: {file.name}</p>}
          <div className="wizard-actions">
            <button className="btn-ghost" onClick={() => setFile(null)}>Clear</button>
            <button className="btn-primary" disabled={!file || loading} onClick={handleUpload}>{loading ? 'Uploading…' : 'Upload'}</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="wizard-panel">
          <h3>Select up to 5 target roles</h3>
          <div className="role-input-row">
            <input value={roleInput} onChange={(e) => setRoleInput(e.target.value)} placeholder="Add a role and press Enter or Add" onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRole())} />
            <button className="btn-primary" onClick={addRole}>Add</button>
          </div>
          <div className="role-chips">
            {roles.map((r, i) => (
              <div key={i} className="chip">
                {r} <button className="chip-remove" onClick={() => removeRole(i)}>×</button>
              </div>
            ))}
          </div>

          <div className="muted-block">Parsed resume preview: {parsedSnippet ? parsedSnippet.slice(0, 280) + '...' : 'No preview available'}</div>
          <div className="wizard-actions">
            <button className="btn-ghost" onClick={() => setStep(1)}>Back</button>
            <button className="btn-primary" disabled={roles.length === 0 || loading} onClick={() => setStep(3)}>Analyze</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="wizard-panel">
          <h3>Analyzing resume with AI</h3>
          <p className="muted-block">This may take a few seconds — the model will return a structured analysis.</p>
          <div className="wizard-actions">
            <button className="btn-ghost" onClick={() => setStep(2)}>Back</button>
            <button className="btn-primary" onClick={handleAnalyze} disabled={loading}>{loading ? 'Analyzing…' : 'Run analysis'}</button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="wizard-panel">
          <h3>Analysis complete</h3>
          {analysis?.parsed ? (
            <pre className="panel-inset">{JSON.stringify(analysis.parsed, null, 2)}</pre>
          ) : (
            <div className="muted-block">Raw analysis: <pre>{analysis?.analysis_raw}</pre></div>
          )}
          <div className="wizard-actions">
            <button className="btn-ghost" onClick={() => setStep(2)}>Back</button>
            <button className="btn-primary" onClick={() => onDone?.()}>Finish</button>
          </div>
        </div>
      )}
    </div>
  )
}
