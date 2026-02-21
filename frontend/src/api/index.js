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

// Versions
export const getVersions = (name) => api.get(`/skills/${name}/versions`)
export const getVersion = (name, ver) => api.get(`/skills/${name}/versions/${ver}`)
export const createVersion = (name, data) => api.post(`/skills/${name}/versions`, data)
export const parseSkillMd = (content) => api.post('/skills/parse-skill-md', { content })

// Teams
export const getTeams = () => api.get('/teams')
export const createTeam = (data) => api.post('/teams', data)

// API Keys
export const getApiKeys = () => api.get('/keys')
export const createApiKey = (data) => api.post('/keys', data)
export const deleteApiKey = (id) => api.delete(`/keys/${id}`)

export default api
