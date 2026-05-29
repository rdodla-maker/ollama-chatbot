import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 180000,
})

/**
 * Health check endpoint
 * @returns {Promise<Object>} Health status
 */
export async function getHealth() {
  const { data } = await api.get('/')
  return data
}

/**
 * Upload resume file
 * @param {File} file - Resume file (PDF, DOC, DOCX)
 * @param {Function} onProgress - Progress callback
 * @returns {Promise<Object>} Upload response with upload_id
 */
export async function uploadResume(file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload-resume', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    },
  })
  return data
}

/**
 * Analyze resume and start application process
 * @param {Object} payload - { upload_id, target_roles }
 * @returns {Promise<Object>} Analysis results
 */
export async function analyzeResume(payload) {
  const { data } = await api.post('/analyze-resume', payload)
  return data
}

/**
 * Get application tracker data
 * @returns {Promise<Object>} Application tracker with applications array
 */
export async function getApplicationTracker() {
  const { data } = await api.get('/application-tracker')
  return data
}
