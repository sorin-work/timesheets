<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { api } from '@/api/client'
import type { Amount, Dashboard } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import { formatDate, formatDuration, formatMoney } from '@/lib/format'
import { useAuth } from '@/stores/auth'
import { useTimer } from '@/stores/timer'

const auth = useAuth()
const timer = useTimer()
const data = ref<Dashboard | null>(null)
const error = ref('')

function amounts(list: Amount[]): string {
  return list.length ? list.map((a) => formatMoney(a.amount, a.currency)).join(' + ') : '—'
}

async function load() {
  try {
    data.value = await api.get<Dashboard>('/dashboard')
  } catch (e) {
    error.value = (e as Error).message
  }
}

watch(() => timer.state.version, load)
onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Hello, {{ auth.state.user?.name }}</h1>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <template v-else-if="data">
      <div class="stats">
        <RouterLink to="/timesheet" class="card stat">
          <span class="muted">Today</span>
          <strong>{{ formatDuration(data.today_seconds) }}</strong>
        </RouterLink>
        <RouterLink to="/timesheet" class="card stat">
          <span class="muted">This week</span>
          <strong>{{ formatDuration(data.week_seconds) }}</strong>
        </RouterLink>
        <RouterLink to="/invoices/new" class="card stat">
          <span class="muted">Ready to invoice</span>
          <strong>{{ amounts(data.unbilled) }}</strong>
          <small class="muted">{{ formatDuration(data.unbilled_seconds) }} unbilled</small>
        </RouterLink>
        <RouterLink to="/invoices?status=sent" class="card stat">
          <span class="muted">Outstanding</span>
          <strong>{{ amounts(data.outstanding) }}</strong>
          <small :class="data.overdue_count ? 'error' : 'muted'">
            {{ data.outstanding_count }} open
            <template v-if="data.overdue_count">, {{ data.overdue_count }} overdue</template>
          </small>
        </RouterLink>
      </div>

      <h2>Recent entries</h2>
      <EmptyState
        v-if="!data.recent.length"
        title="Nothing tracked yet"
        message="Pick a project in the bar above and press Start."
      />
      <table v-else class="table">
        <tbody>
          <tr v-for="e in data.recent" :key="e.id">
            <td>
              {{ e.description || '(no description)' }}
              <div class="muted small">{{ e.client_name }} · {{ e.project_name }}</div>
            </td>
            <td class="muted">{{ formatDate(e.started_at) }}</td>
            <td class="num">{{ e.running ? 'running' : formatDuration(e.duration_seconds) }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  text-decoration: none;
  color: inherit;
}

.stat:hover {
  border-color: var(--primary);
}

.stat strong {
  font-size: 1.375rem;
}

h2 {
  font-size: 1.125rem;
}

.small {
  font-size: 0.75rem;
}
</style>
