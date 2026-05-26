import { useState } from 'react'
import { uploadPdf } from '../api/client'

export default function PdfUpload() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleUpload = async () => {
    if (!file || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    setProgress(0)

    try {
      const data = await uploadPdf(file, setProgress)
      setResult(data)
      setFile(null)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed')
    } finally {
      setLoading(false)
      setProgress(0)
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Upload PDF</h2>
      </div>

      <p className="panel-desc">
        Upload a PDF to index it for RAG chat. Text is chunked and stored in
        ChromaDB.
      </p>

      <div className="upload-zone">
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          disabled={loading}
        />
        {file && <p className="file-name">Selected: {file.name}</p>}
      </div>

      {loading && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
          <span>{progress}%</span>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="success-banner">
          {result.message} — {result.chunks} chunks indexed.
          {result.document_id && (
            <span className="doc-id"> ID: {result.document_id.slice(0, 8)}…</span>
          )}
        </div>
      )}

      <button
        type="button"
        className="btn-primary"
        onClick={handleUpload}
        disabled={!file || loading}
      >
        {loading ? 'Uploading…' : 'Upload & index'}
      </button>
    </div>
  )
}
