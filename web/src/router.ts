import { createRouter, createWebHistory } from 'vue-router'

import { setUnauthorizedHandler } from '@/api/client'
import AppLayout from '@/components/AppLayout.vue'
import { useAuth } from '@/stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      meta: { title: 'Sign in' },
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/signup',
      name: 'signup',
      meta: { title: 'Create account' },
      component: () => import('@/views/SignupView.vue'),
    },
    {
      path: '/',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'home',
          meta: { title: 'Dashboard' },
          component: () => import('@/views/HomeView.vue'),
        },
        {
          path: 'timesheet',
          name: 'timesheet',
          meta: { title: 'Timesheet' },
          component: () => import('@/views/TimesheetView.vue'),
        },
        {
          path: 'entries',
          name: 'entries',
          meta: { title: 'Time entries' },
          component: () => import('@/views/EntriesView.vue'),
        },
        {
          path: 'invoices',
          name: 'invoices',
          meta: { title: 'Invoices' },
          component: () => import('@/views/InvoicesView.vue'),
        },
        {
          path: 'invoices/new',
          name: 'invoice-new',
          meta: { title: 'New invoice' },
          component: () => import('@/views/InvoiceNewView.vue'),
        },
        {
          path: 'invoices/:id(\\d+)',
          name: 'invoice',
          meta: { title: 'Invoice' },
          component: () => import('@/views/InvoiceView.vue'),
        },
        {
          path: 'reports',
          name: 'reports',
          meta: { title: 'Reports' },
          component: () => import('@/views/ReportsView.vue'),
        },
        {
          path: ':pathMatch(.*)*',
          name: 'not-found',
          meta: { title: 'Not found' },
          component: () => import('@/views/NotFoundView.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          meta: { title: 'Settings' },
          component: () => import('@/views/SettingsView.vue'),
        },
        {
          path: 'clients',
          name: 'clients',
          meta: { title: 'Clients' },
          component: () => import('@/views/ClientsView.vue'),
        },
        {
          path: 'projects',
          name: 'projects',
          meta: { title: 'Projects' },
          component: () => import('@/views/ProjectsView.vue'),
        },
      ],
    },
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

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} · Timesheets` : 'Timesheets'
})

setUnauthorizedHandler(() => {
  useAuth().forget()
  if (router.currentRoute.value.name !== 'login') router.push({ name: 'login' })
})
