import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
})

export const getDashboardCurrent = () => api.get('/dashboard/current')
export const getDashboardForecast = () => api.get('/dashboard/forecast')
export const runFullEpisode = () => api.post('/agent/run_full')
export const getAgentStatus = () => api.get('/agent/status')
export const getHistory = (limit = 24) => api.get(`/history/operations?limit=${limit}`)
export const getComparison = () => api.get('/history/comparison')
export const getProfitSummary = () => api.get('/history/profit')

export default api