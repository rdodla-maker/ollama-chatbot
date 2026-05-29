import { useState } from 'react'
import Topbar from '../components/Topbar'

export default function ResumeAnalyzer({ status, latestResult, onNavigate }) {
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isDragActive, setIsDragActive] = useState(false)

  // Mock data - replace with actual state from parent or API
  const currentResume = latestResult?.resume_name || uploadedFile?.name || 'No resume uploaded yet'
  const lastUpdated = latestResult?.upload_date || new Date().toLocaleDateString()
  const hasResume = latestResult || uploadedFile

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  function handleDownload() {
    // Implement download logic here
    alert('Download functionality to be implemented')
  }

  return (
    <div className="page page-wide">
      <Topbar
        title="Resume"
        subtitle="Manage your resume and start applying to jobs"
        status={status}
      />

      <section className="panel-card resume-management-card">
        <div className="panel-card-header">
          <div>
            <span className="section-kicker">Your Resume</span>
            <h3>Current resume</h3>
          </div>
        </div>

        {hasResume ? (
          <div className="resume-status-card panel-inset">
            <div className="resume-status-header">
              <div className="resume-status-icon">📄</div>
              <div className="resume-status-details">
                <h4>{currentResume}</h4>
                <p className="resume-status-date">Last updated: {lastUpdated}</p>
              </div>
            </div>
            <div className="resume-status-actions">
              <button type="button" className="btn-ghost" onClick={handleDownload}>
                ⬇ Download Optimized Resume
              </button>
            </div>
          </div>
        ) : (
          <div className="empty-state resume-empty-state">
            <div className="empty-state-icon">📄</div>
            <h3>No resume uploaded</h3>
            <p>Upload your resume to get started with AI-powered job applications.</p>
          </div>
        )}

        <div className="resume-upload-section">
          <h4>Replace or upload resume</h4>
          <p className="muted-block">Upload a new resume to update your profile and start applying.</p>
          
          <label
            className={`upload-dropzone panel-inset ${isDragActive ? 'drag-active' : ''} ${uploadedFile ? 'has-file' : ''}`}
            onDragEnter={(e) => { e.preventDefault(); setIsDragActive(true) }}
            onDragOver={(e) => { e.preventDefault(); setIsDragActive(true) }}
            onDragLeave={(e) => { e.preventDefault(); setIsDragActive(false) }}
            onDrop={handleDrop}
          >
            <input 
              className="sr-only-input" 
              type="file" 
              accept=".pdf,.doc,.docx" 
              onChange={handleFileChange} 
            />
            <span className="upload-dropzone-icon">+</span>
            <strong>{uploadedFile ? uploadedFile.name : 'Drag and drop your resume here'}</strong>
            <span>{uploadedFile ? 'Ready to upload' : 'or click to browse for a file'}</span>
            <span className="upload-hint">Accepts PDF, DOC, or DOCX</span>
          </label>

          {uploadedFile && (
            <div className="resume-upload-actions">
              <button type="button" className="btn-ghost" onClick={() => setUploadedFile(null)}>
                Cancel
              </button>
              <button type="button" className="btn-primary" onClick={() => onNavigate?.('resume')}>
                Upload & Start Apply
              </button>
            </div>
          )}
        </div>
      </section>

      <section className="panel-card resume-tips-card">
        <div className="panel-card-header">
          <div>
            <span className="section-kicker">Tips</span>
            <h3>Optimize your resume</h3>
          </div>
        </div>
        <div className="resume-tips-grid">
          <div className="resume-tip-card">
            <strong>📊 Use numbers</strong>
            <p>Quantify your achievements with specific metrics and results.</p>
          </div>
          <div className="resume-tip-card">
            <strong>🎯 Match keywords</strong>
            <p>Include relevant skills and technologies from job descriptions.</p>
          </div>
          <div className="resume-tip-card">
            <strong>✨ Keep it concise</strong>
            <p>Focus on impact and relevant experience for your target roles.</p>
          </div>
        </div>
      </section>
    </div>
  )
}
