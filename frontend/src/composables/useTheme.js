import { ref } from 'vue'

const THEME_KEY = 'skills-hub-theme'
const theme = ref('light')

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(nextTheme) {
  theme.value = nextTheme
  const root = document.documentElement
  root.classList.toggle('dark', nextTheme === 'dark')
  root.style.colorScheme = nextTheme
}

function initTheme() {
  const savedTheme = localStorage.getItem(THEME_KEY)
  applyTheme(savedTheme || getSystemTheme())
}

function toggleTheme() {
  const nextTheme = theme.value === 'dark' ? 'light' : 'dark'
  applyTheme(nextTheme)
  localStorage.setItem(THEME_KEY, nextTheme)
}

function setTheme(nextTheme) {
  applyTheme(nextTheme)
  localStorage.setItem(THEME_KEY, nextTheme)
}

export function useTheme() {
  return {
    theme,
    initTheme,
    toggleTheme,
    setTheme,
  }
}
