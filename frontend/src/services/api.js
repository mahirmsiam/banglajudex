import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Search API
export const searchJudgments = async (query, filters = {}, topK = 10) => {
  const response = await api.post('/search', {
    query,
    filters: Object.keys(filters).length > 0 ? filters : null,
    top_k: topK
  })
  return response.data
}

// Conversational Query API
export const queryJudgments = async (query, filters = {}, conversationHistory = []) => {
  const response = await api.post('/query', {
    query,
    filters: Object.keys(filters).length > 0 ? filters : null,
    conversation_history: conversationHistory
  })
  return response.data
}

// Get cases list
export const getCases = async (skip = 0, limit = 20, filters = {}) => {
  const params = new URLSearchParams({ skip, limit })
  if (filters.court) params.append('court', filters.court)
  if (filters.year) params.append('year', filters.year)
  if (filters.case_type) params.append('case_type', filters.case_type)
  
  const response = await api.get(`/cases?${params}`)
  return response.data
}

// Get single case
export const getCase = async (caseId) => {
  const response = await api.get(`/cases/${caseId}`)
  return response.data
}

// Get paragraph
export const getParagraph = async (paragraphId) => {
  const response = await api.get(`/paragraphs/${paragraphId}`)
  return response.data
}

// Get filter options
export const getFilterOptions = async () => {
  const response = await api.get('/filters')
  return response.data
}

// Ingestion APIs
export const startIngestion = async () => {
  const response = await api.post('/ingest/start')
  return response.data
}

export const getIngestionStatus = async () => {
  const response = await api.get('/ingest/status')
  return response.data
}

export const getIngestionLogs = async (skip = 0, limit = 50) => {
  const response = await api.get(`/ingest/logs?skip=${skip}&limit=${limit}`)
  return response.data
}

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

export default api
