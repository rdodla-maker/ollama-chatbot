import { useState } from 'react'
import Topbar from '../components/Topbar'
import JobApplicationForm from '../components/JobApplicationForm'
import ResultTabs from '../components/ResultTabs'
import { generateApplicationPack } from '../services/jobApplicationService'

export default function JobApplications({ status, onGenerated }) {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (payload) => {
    setLoading(true)
    setError('')
    try {
      const data = await generateApplicationPack(payload)
      setResults(data)
      onGenerated?.(data)
      return data
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to generate application materials.'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page page-wide">
      <Topbar
        title="Job Applications"
        subtitle="Fill in one job brief and generate your complete application pack."
        status={status}
      />

      <section className="page-intro-card panel-inset">
        <div>
          <span className="section-kicker">Application studio</span>
          <h2>Generate tailored assets with one guided input flow.</h2>
        </div>
        <p>
          Feed the assistant the role, job description, your current resume text, and the tone you want.
          The right panel updates with polished AI output.
        </p>
      </section>

      <div className="panel-grid two-column application-layout">
        <JobApplicationForm onSubmit={handleSubmit} loading={loading} error={error} />
        <ResultTabs results={results} loading={loading} />
      </div>
    </div>
  )
}
