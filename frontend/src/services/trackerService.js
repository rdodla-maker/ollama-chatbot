import { getApplicationTracker } from '../api/api'

export async function fetchTrackerItems() {
  const data = await getApplicationTracker()
  return data.applications || []
}