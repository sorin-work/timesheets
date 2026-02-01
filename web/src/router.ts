import { createRouter, createWebHistory } from 'vue-router'

import { setUnauthorizedHandler } from '@/api/client'
import { useAuth } from '@/stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/signup', name: 'signup', component: () => import('@/views/SignupView.vue') },
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

const PUBLIC = new Set(['login', 'signup'])

router.beforeEach(async (to) => {
  const auth = useAuth()
  await auth.load()
  const isPublic = PUBLIC.has(String(to.name))
  if (!auth.state.user && !isPublic) {
    return { name: 'login', query: to.fullPath === '/' ? {} : { next: to.fullPath } }
  }
  if (auth.state.user && isPublic) return { name: 'home' }
})

setUnauthorizedHandler(() => {
  useAuth().forget()
  if (router.currentRoute.value.name !== 'login') router.push({ name: 'login' })
})
