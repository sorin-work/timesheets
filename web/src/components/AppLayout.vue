<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import LongTimerNotice from '@/components/LongTimerNotice.vue'
import ShortcutsHelp from '@/components/ShortcutsHelp.vue'
import TimerBar from '@/components/TimerBar.vue'
import { setTheme, storedTheme, type Theme } from '@/lib/theme'
import { useAuth } from '@/stores/auth'

const auth = useAuth()
const router = useRouter()
const menuOpen = ref(false)
const theme = ref<Theme>(storedTheme())

function changeTheme() {
  setTheme(theme.value)
}

const nav = [
  { to: '/', label: 'Dashboard' },
  { to: '/timesheet', label: 'Timesheet' },
  { to: '/entries', label: 'Entries' },
  { to: '/invoices', label: 'Invoices' },
  { to: '/clients', label: 'Clients' },
  { to: '/projects', label: 'Projects' },
  { to: '/reports', label: 'Reports' },
  { to: '/settings', label: 'Settings' },
]

const route = useRoute()

function isCurrent(to: string): boolean {
  return to === '/' ? route.path === '/' : route.path === to || route.path.startsWith(`${to}/`)
}

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar" :class="{ open: menuOpen }">
      <div class="brand">
        <img src="/favicon.svg" alt="" width="24" height="24" />
        <span>Timesheets</span>
      </div>
      <nav>
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ current: isCurrent(item.to) }"
          @click="menuOpen = false"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
      <div class="account">
        <span class="muted">{{ auth.state.user?.name }}</span>
        <select v-model="theme" aria-label="Theme" @change="changeTheme">
          <option value="system">System theme</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
        <button type="button" @click="logout">Sign out</button>
      </div>
    </aside>
    <div class="content">
      <header class="topbar">
        <button type="button" class="menu-toggle" aria-label="Menu" @click="menuOpen = !menuOpen">
          ☰
        </button>
        <TimerBar />
      </header>
      <LongTimerNotice />
      <ShortcutsHelp />
      <main class="page">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 14rem 1fr;
  min-height: 100vh;
}

.sidebar {
  background: #111827;
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 1rem 0.75rem;
  gap: 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  padding: 0 0.5rem;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  flex: 1;
}

.nav-link {
  color: inherit;
  text-decoration: none;
  padding: 0.5rem 0.625rem;
  border-radius: 6px;
}

.nav-link:hover {
  background: #1f2937;
}

.nav-link.current {
  background: #374151;
  color: white;
}

.account {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0 0.5rem;
}

.account select {
  background: #1f2937;
  color: inherit;
  border-color: #374151;
}

.account button {
  background: transparent;
  color: inherit;
  border-color: #374151;
}

.content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 2rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  position: sticky;
  top: 0;
  z-index: 10;
}

.menu-toggle {
  display: none;
}

.page {
  padding: 1.5rem 2rem;
  max-width: 72rem;
  width: 100%;
}

@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: 15rem;
    transform: translateX(-100%);
    transition: transform 0.2s;
    z-index: 20;
  }

  .sidebar.open {
    transform: none;
  }

  .topbar {
    padding: 0.5rem 1rem;
  }

  .menu-toggle {
    display: block;
  }

  .page {
    padding: 1rem;
  }
}
</style>
