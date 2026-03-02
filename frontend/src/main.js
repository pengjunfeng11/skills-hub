import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './assets/main.css'
import { useTheme } from './composables/useTheme'

const app = createApp(App)
const pinia = createPinia()
const { initTheme } = useTheme()

initTheme()

app.use(pinia)
app.use(router)

app.mount('#app')
