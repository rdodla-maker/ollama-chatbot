/**
 * Check if file is an allowed resume format
 * @param {File} file - File object to validate
 * @returns {boolean} True if file is PDF, DOC, or DOCX
 */
export function isAllowedResumeFile(file) {
  if (!file) return false
  const name = file.name.toLowerCase()
  return name.endsWith('.pdf') || name.endsWith('.doc') || name.endsWith('.docx')
}

/**
 * Get file extension
 * @param {string} filename - File name
 * @returns {string} File extension (e.g., "pdf")
 */
export function getFileExtension(filename) {
  if (!filename) return ''
  const parts = filename.split('.')
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : ''
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted size (e.g., "2.5 MB")
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

/**
 * Validate email format
 * @param {string} email - Email address to validate
 * @returns {boolean} True if email format is valid
 */
export function isValidEmail(email) {
  if (!email) return false
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate non-empty string
 * @param {string} value - String to validate
 * @param {number} minLength - Minimum length (default: 1)
 * @returns {boolean} True if string is valid
 */
export function isNonEmptyString(value, minLength = 1) {
  return typeof value === 'string' && value.trim().length >= minLength
}
