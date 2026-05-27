import { generateApplication } from '../api/api'

export async function generateApplicationPack(payload) {
  return generateApplication(payload)
}