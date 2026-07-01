<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api } from '@/api/client'
import type { Client, ClientSummary, InvoiceSummary, Project } from '@/api/types'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatDate, formatDuration, formatMoney } from '@/lib/format'

const route = useRoute()
const id = Number(route.params.id)

const client = ref<Client | null>(null)
const summary = ref<ClientSummary | null>(null)
const projects = ref<Project[]>([])
const invoices = ref<InvoiceSummary[]>([])
const error = ref('')

onMounted(async () => {
  try {
    ;[client.value, summary.value, projects.value, invoices.value] = await Promise.all([
      api.get<Client>(`/clients/${id}`),
      api.get<ClientSummary>(`/clients/${id}/summary`),
      api.get<Project[]>('/projects', { client_id: id, include_archived: true }),
      api.get<InvoiceSummary[]>('/invoices', { client_id: id }),
    ])
  } catch (e) {
    error.value = (e as Error).message
  }
})
</script>

<template>
  <section>
    <p v-if="error" class="error">{{ error }}</p>
    <template v-else-if="client && summary">
      <div class="page-header">
        <div>
          <h1>{{ client.name }}</h1>
          <p class="muted">
            {{ client.email ?? 'No billing email' }} ·
            {{
              client.hourly_rate
                ? `${formatMoney(client.hourly_rate, client.currency)}/h`
                : 'no rate'
            }}
          </p>
        </div>
        <RouterLink :to="`/entries?client_id=${client.id}`">See time entries</RouterLink>
      </div>

      <div class="stats">
        <div class="card stat">
          <span class="muted">Tracked</span>
          <strong>{{ formatDuration(summary.tracked_seconds) }}</strong>
          <small v-if="summary.last_tracked_at" class="muted">
            last {{ formatDate(summary.last_tracked_at) }}
          </small>
        </div>
        <div class="card stat">
          <span class="muted">Not invoiced yet</span>
          <strong>{{ formatDuration(summary.unbilled_seconds) }}</strong>
        </div>
        <div class="card stat">
          <span class="muted">Paid</span>
          <strong>{{ formatMoney(summary.paid, summary.currency) }}</strong>
        </div>
        <div class="card stat">
          <span class="muted">Outstanding</span>
          <strong>{{ formatMoney(summary.outstanding, summary.currency) }}</strong>
        </div>
      </div>

      <h2>Projects</h2>
      <p v-if="!projects.length" class="muted">No projects yet.</p>
      <ul v-else class="projects">
        <li v-for="p in projects" :key="p.id">
          <span class="dot" :style="{ background: p.color }" />
          {{ p.name }}
          <span v-if="p.archived_at" class="badge">archived</span>
          <span class="muted">· {{ formatDuration(p.used_seconds) }}</span>
        </li>
      </ul>

      <h2>Invoices</h2>
      <p v-if="!invoices.length" class="muted">No invoices yet.</p>
      <table v-else class="table">
        <tbody>
          <tr v-for="inv in invoices" :key="inv.id">
            <td>
              <RouterLink :to="`/invoices/${inv.id}`">{{ inv.number }}</RouterLink>
            </td>
            <td>{{ formatDate(inv.issue_date) }}</td>
            <td><StatusBadge :status="inv.status" /></td>
            <td class="num">{{ formatMoney(inv.total, inv.currency) }}</td>
          </tr>
        </tbody>
      </table>
    </template>
    <p v-else class="muted">Loading…</p>
  </section>
</template>

<style scoped>
.page-header p {
  margin: 0.25rem 0 0;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat strong {
  font-size: 1.25rem;
}

h2 {
  font-size: 1.125rem;
  margin: 1.5rem 0 0.5rem;
}

.projects {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.dot {
  display: inline-block;
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 999px;
  margin-right: 0.375rem;
}
</style>
