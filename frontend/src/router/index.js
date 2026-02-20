import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'skills', name: 'SkillList', component: () => import('../views/SkillList.vue') },
      { path: 'skills/new', name: 'SkillCreate', component: () => import('../views/SkillEditor.vue') },
      { path: 'skills/:name', name: 'SkillDetail', component: () => import('../views/SkillDetail.vue') },
      { path: 'skills/:name/edit', name: 'SkillEdit', component: () => import('../views/SkillEditor.vue') },
      { path: 'teams', name: 'Teams', component: () => import('../views/TeamView.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/Settings.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.token) {
    return { name: 'Login' }
  }
})

export default router
