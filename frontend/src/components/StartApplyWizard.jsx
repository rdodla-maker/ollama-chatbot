import { useMemo, useState } from 'react'
import { uploadResume as apiUploadResume, analyzeResume as apiAnalyzeResume } from '../api/api'
import { isAllowedResumeFile } from '../utils/validators'

const PROGRESS_STATES = [
  'Resume Analyzed',
  'Searching Jobs',
  'Generating Applications',
  'Applying',
]

export default function StartApplyWizard({ onDone }) {
  const [step, setStep] = useState(1)
  const [file, setFile] = useState(null)
  const [uploadId, setUploadId] = useState(null)
  const [parsedSnippet, setParsedSnippet] = useState('')
  const [roles, setRoles] = useState([])
  const [roleInput, setRoleInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState('')
  const [isDragActive, setIsDragActive] = useState(false)
  const [progressIndex, setProgressIndex] = useState(0)

  const progressLabel = PROGRESS_STATES[Math.min(progressIndex, PROGRESS_STATES.length - 1)]
  const canAddMoreRoles = roles.length < 5
  const roleSummary = useMemo(() => roles.join(', '), [roles])

  function applyFile(nextFile) {
    setError('')
    setUploadSuccess('')
    if (!nextFile) {
      setFile(null)
      return
    }
    if (!isAllowedResumeFile(nextFile)) {
      setFile(null)
      setUploadId(null)
      setParsedSnippet('')
      setError('Please upload a PDF, DOC, or DOCX resume.')
      return
    }
    setFile(nextFile)
  }

  function onFileChange(e) {
    applyFile(e.target.files?.[0] || null)
  }

  function onDrop(event) {
    event.preventDefault()
    setIsDragActive(false)
    applyFile(event.dataTransfer.files?.[0] || null)
  }

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const res = await apiUploadResume(file, (p) => {})
      setUploadId(res.upload_id)
      setParsedSnippet(res.parsed_snippet || '')
      setUploadSuccess('Resume uploaded successfully.')
      setStep(2)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Unable to upload your resume right now.')
    } finally {
      setLoading(false)
    }
  }

  function addRole() {
    setError('')
    const val = roleInput.trim()
    if (!val) return
    if (roles.includes(val)) {
      setRoleInput('')
      return
    }
    if (roles.length >= 5) {
      setError('You can add up to 5 job roles.')
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
    setError('')
    setProgressIndex(0)
    const timer = window.setInterval(() => {
      setProgressIndex((current) => (current < PROGRESS_STATES.length - 1 ? current + 1 : current))
    }, 1100)

    try {
      const payload = { upload_id: uploadId, target_roles: roles }
      const res = await apiAnalyzeResume(payload)
      setAnalysis(res)
      setStep(4)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Unable to start applying right now.')
    } finally {
      window.clearInterval(timer)
      setLoading(false)
    }
  }

  return (
    <div className="start-apply-wizard">
      <div className="wizard-step-indicator">Step {step} of 3</div>
      {error ? <p className="form-error">{error}</p> : null}
      {uploadSuccess ? <p className="form-success">{uploadSuccess}</p> : null}

      {step === 1 && (
        <div className="wizard-panel">
          <h3>Upload your resume</h3>
          <p className="muted-block">Use a PDF or DOCX file to start your application flow.</p>
          <label
            className={`upload-dropzone panel-inset ${isDragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
            onDragEnter={(event) => {
              event.preventDefault()
              setIsDragActive(true)
            }}
            onDragOver={(event) => {
              event.preventDefault()
              setIsDragActive(true)
            }}
            onDragLeave={(event) => {
              event.preventDefault()
              setIsDragActive(false)
            }}
            onDrop={onDrop}
          >
            <input className="sr-only-input" type="file" accept=".pdf,.doc,.docx" onChange={onFileChange} />
            <span className="upload-dropzone-icon">+</span>
            <strong>{file ? file.name : 'Drag and drop your resume here'}</strong>
            <span>{file ? 'Ready to upload' : 'or click to browse for a file'}</span>
          </label>
          {file ? (
            <div className="wizard-preview panel-inset">
              <strong>Uploaded file</strong>
              <span>{file.name}</span>
            </div>
          ) : null}
          <div className="wizard-actions">
            <button className="btn-ghost" onClick={() => applyFile(null)}>Clear</button>
            <button className="btn-primary" disabled={!file || loading} onClick={handleUpload}>{loading ? 'Uploading…' : 'Upload'}</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="wizard-panel">
          <h3>Add target job titles</h3>
          <p className="muted-block">Pick up to five roles so the assistant can tailor your resume setup.</p>
          <div className="role-input-row">
            <input value={roleInput} onChange={(e) => setRoleInput(e.target.value)} placeholder="Add a role and press Enter or Add" onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRole())} />
            <button className="btn-primary" onClick={addRole} disabled={!roleInput.trim() || !canAddMoreRoles}>Add</button>
          </div>
          <div className="role-input-meta">
            <span>{roles.length}/5 roles added</span>
            <span>{canAddMoreRoles ? 'Add up to five target roles.' : 'Maximum reached.'}</span>
          </div>
          <div className="role-chips">
            {roles.map((r, i) => (
              <div key={i} className="chip">
                {r} <button className="chip-remove" onClick={() => removeRole(i)}>×</button>
              </div>
            ))}
          </div>

          <div className="wizard-preview panel-inset">
            <strong>Resume preview</strong>
            <span>{parsedSnippet ? `${parsedSnippet.slice(0, 280)}...` : 'Your resume preview will appear here after upload.'}</span>
          </div>
          <div className="wizard-actions">
            <button className="btn-ghost" onClick={() => setStep(1)}>Back</button>
            <button className="btn-primary" disabled={roles.length === 0 || loading} onClick={() => setStep(3)}>Continue</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="wizard-panel">
          <h3>Start Apply</h3>
          <p className="muted-block">We’ll prepare your resume for the roles you selected and move you into the applications list.</p>
          <div className="wizard-preview panel-inset">
            <strong>Selected roles</strong>
            <span>{roleSummary}</span>
          </div>
          {loading ? (
            <div className="wizard-progress panel-inset">
              <div className="wizard-progress-bar"><span /></div>
              <strong>{progressLabel}</strong>
              <span>The assistant is working in the background. You only need to track the results.</span>
            </div>
          ) : null}
          <div className="wizard-actions">
            <button className="btn-ghost" onClick={() => setStep(2)}>Back</button>
            <button className="btn-primary btn-primary-large" onClick={handleAnalyze} disabled={loading}>{loading ? 'Starting…' : 'Start Apply'}</button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="wizard-panel wizard-success-panel">
          <div className="success-icon">✓</div>
          <h3>All set! AI is working for you.</h3>
          <p className="muted-block">
            Your AI assistant is now searching for jobs and preparing tailored applications. 
            You can track progress in your Applications hub.
          </p>
          <div className="wizard-success-grid">
            <div className="wizard-preview panel-inset">
              <strong>Resume uploaded</strong>
              <span>{file?.name || 'Uploaded successfully'}</span>
            </div>
            <div className="wizard-preview panel-inset">
              <strong>Target roles</strong>
              <span>{roles.join(', ')}</span>
            </div>
          </div>
          <div className="success-summary panel-inset success-summary-card">
            <h4>What's happening now:</h4>
            <ul className="success-steps">
              <li>✓ Resume analyzed and optimized</li>
              <li>🔄 Searching for matching job opportunities</li>
              <li>🔄 Generating personalized applications</li>
            </ul>
          </div>
          <div className="wizard-actions">
            <button className="btn-primary btn-primary-large" onClick={() => onDone?.(analysis)}>
              View Applications
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
