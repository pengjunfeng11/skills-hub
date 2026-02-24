import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const url = err.config?.url || ''
      // Don't redirect on login/register failures — let the page show the error
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        const auth = useAuthStore()
        auth.logout()
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// Auth
export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const getMe = () => api.get('/auth/me')

// Skills
export const getSkills = (params) => api.get('/skills', { params })
export const getSkill = (name) => api.get(`/skills/${name}`)
export const createSkill = (data) => api.post('/skills', data)
export const updateSkill = (name, data) => api.put(`/skills/${name}`, data)
export const deleteSkill = (name) => api.delete(`/skills/${name}`)
export const subscribeSkill = (name) => api.post(`/skills/${name}/subscribe`)
export const unsubscribeSkill = (name) => api.delete(`/skills/${name}/subscribe`)

// Versions
export const getVersions = (name) => api.get(`/skills/${name}/versions`)
export const getVersion = (name, ver) => api.get(`/skills/${name}/versions/${ver}`)
export const createVersion = (name, data) => api.post(`/skills/${name}/versions`, data)
export const parseSkillMd = (content) => api.post('/skills/parse-skill-md', { content })

// Teams
export const getTeams = () => api.get('/teams')
export const getTeam = (slug) => api.get(`/teams/${slug}`)
export const getMyTeams = () => api.get('/teams/my')
export const createTeam = (data) => api.post('/teams', data)
export const joinTeam = (slug) => api.post(`/teams/${slug}/join`)
export const leaveTeam = (slug) => api.post(`/teams/${slug}/leave`)
export const removeTeamMember = (slug, userId) => api.delete(`/teams/${slug}/members/${userId}`)

// API Keys
export const getApiKeys = () => api.get('/keys')
export const getApiKeyDetail = (id) => api.get(`/keys/${id}`)
export const createApiKey = (data) => api.post('/keys', data)
export const updateApiKey = (id, data) => api.put(`/keys/${id}`, data)
export const deleteApiKey = (id) => api.delete(`/keys/${id}`)

// Stats
export const getStatsOverview = () => api.get('/stats/overview')
export const getStatsPopular = (params) => api.get('/stats/popular', { params })
export const getStatsTrend = (params) => api.get('/stats/trend', { params })

export default api
