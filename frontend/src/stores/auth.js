import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMe } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  function setToken(t) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await getMe()
      user.value = res.data
    } catch {
      logout()
    }
  }

  return { token, user, setToken, logout, fetchUser }
})
