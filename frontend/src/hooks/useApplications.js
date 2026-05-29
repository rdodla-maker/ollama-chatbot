import { useMemo } from 'react'

/**
 * Custom hook for application filtering and categorization
 * @param {Array} applications - Raw application list
 * @param {string} searchQuery - Search query string
 * @returns {Object} Categorized and filtered applications
 */
export function useApplications(applications = [], searchQuery = '') {
  return useMemo(() => {
    // Filter by search query
    const search = searchQuery.trim().toLowerCase()
    const filtered = applications.filter((item) => {
      if (!search) return true
      const haystack = `${item.company || ''} ${item.role || ''}`.toLowerCase()
      return haystack.includes(search)
    })

    // Categorize by status
    const categorized = {
      pending: filtered
        .filter((item) => item.status === 'pending')
        .sort((a, b) => `${b.application_date || ''}`.localeCompare(`${a.application_date || ''}`)),
      
      applied: filtered
        .filter((item) => item.status === 'applied')
        .sort((a, b) => `${b.application_date || ''}`.localeCompare(`${a.application_date || ''}`)),
      
      interview: filtered
        .filter((item) => item.status === 'interview')
        .sort((a, b) => `${b.application_date || ''}`.localeCompare(`${a.application_date || ''}`)),
      
      rejected: filtered
        .filter((item) => item.status === 'rejected')
        .sort((a, b) => `${b.application_date || ''}`.localeCompare(`${a.application_date || ''}`))
    }

    // Calculate counts
    const counts = {
      total: applications.length,
      pending: categorized.pending.length,
      applied: categorized.applied.length,
      interview: categorized.interview.length,
      rejected: categorized.rejected.length
    }

    return {
      categorized,
      counts,
      filtered,
      isEmpty: applications.length === 0,
      hasResults: filtered.length > 0
    }
  }, [applications, searchQuery])
}
