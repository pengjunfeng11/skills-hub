<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <!-- Logo -->
      <div class="h-16 flex items-center px-6 border-b border-gray-100">
        <span class="material-icons-round text-primary text-[28px] mr-2">hub</span>
        <span class="text-lg font-bold text-gray-900">Skills Hub</span>
      </div>

      <!-- Nav -->
      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors no-underline',
            isActive(item.path)
              ? 'bg-primary text-white'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          ]"
        >
          <span class="material-icons-round text-[20px]">{{ item.icon }}</span>
          {{ item.label }}
        </router-link>
      </nav>

      <!-- Bottom -->
      <div class="px-3 py-4 border-t border-gray-100 space-y-1">
        <router-link
          to="/setup"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors no-underline',
            isActive('/setup')
              ? 'bg-primary text-white'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          ]"
        >
          <span class="material-icons-round text-[20px]">integration_instructions</span>
          集成指南
        </router-link>
        <router-link
          to="/settings"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors no-underline',
            isActive('/settings')
              ? 'bg-primary text-white'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          ]"
        >
          <span class="material-icons-round text-[20px]">settings</span>
          设置
        </router-link>
      </div>
    </aside>

    <!-- Main area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-end px-6 shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold">
            {{ auth.user?.username?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
          <span class="text-sm font-medium text-gray-700">{{ auth.user?.username }}</span>
          <button
            @click="handleLogout"
            class="ml-2 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
            title="退出"
          >
            <span class="material-icons-round text-[20px]">logout</span>
          </button>
        </div>
      </header>

      <!-- Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navItems = [
  { path: '/', icon: 'dashboard', label: '概览' },
  { path: '/skills', icon: 'auto_awesome', label: 'Skills' },
  { path: '/teams', icon: 'groups', label: '团队' },
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

onMounted(() => {
  auth.fetchUser()
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
