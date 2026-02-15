import { createRouter, createWebHistory } from 'vue-router'

import { setUnauthorizedHandler } from '@/api/client'
import AppLayout from '@/components/AppLayout.vue'
import { useAuth } from '@/stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/signup', name: 'signup', component: () => import('@/views/SignupView.vue') },
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        {
          path: 'timesheet',
          name: 'timesheet',
          component: () => import('@/views/TimesheetView.vue'),
        },
        { path: 'entries', name: 'entries', component: () => import('@/views/EntriesView.vue') },
        {
          path: 'invoices',
          name: 'invoices',
          component: () => import('@/views/InvoicesView.vue'),
        },
        {
          path: 'invoices/new',
          name: 'invoice-new',
          component: () => import('@/views/InvoiceNewView.vue'),
        },
        {
          path: 'invoices/:id(\\d+)',
          name: 'invoice',
          component: () => import('@/views/InvoiceView.vue'),
        },
        { path: 'clients', name: 'clients', component: () => import('@/views/ClientsView.vue') },
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/views/ProjectsView.vue'),
        },
      ],
    },
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
