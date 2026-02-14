<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api/client'
import type { InvoiceStatus, InvoiceSummary } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatDate, formatMoney } from '@/lib/format'

const route = useRoute()
const router = useRouter()

const TABS: { value: InvoiceStatus | ''; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'draft', label: 'Drafts' },
  { value: 'sent', label: 'Sent' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'paid', label: 'Paid' },
]

const invoices = ref<InvoiceSummary[]>([])
const loading = ref(true)
const error = ref('')
const status = ref<InvoiceStatus | ''>((route.query.status as InvoiceStatus) ?? '')

async function load() {
  loading.value = true
  error.value = ''
  try {
    invoices.value = await api.get<InvoiceSummary[]>('/invoices', { status: status.value })
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

watch(status, (value) => {
  router.replace({ query: value ? { status: value } : {} })
  load()
})

onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Invoices</h1>
      <RouterLink class="button primary" to="/invoices/new">New invoice</RouterLink>
    </div>

    <div class="tabs" role="tablist">
      <button
        v-for="tab in TABS"
        :key="tab.value"
        type="button"
        role="tab"
        :aria-selected="status === tab.value"
        :class="{ active: status === tab.value }"
        @click="status = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading" class="muted">Loading…</p>
    <EmptyState
      v-else-if="!invoices.length"
      :title="status ? `No ${status} invoices` : 'No invoices yet'"
      message="Invoices are generated from your unbilled time."
    >
      <RouterLink v-if="!status" to="/invoices/new">Create your first invoice</RouterLink>
    </EmptyState>
    <table v-else class="table">
      <thead>
        <tr>
          <th>Number</th>
          <th>Client</th>
          <th>Issued</th>
          <th>Due</th>
          <th>Status</th>
          <th class="num">Total</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="inv in invoices" :key="inv.id">
          <td>
            <RouterLink :to="`/invoices/${inv.id}`">{{ inv.number }}</RouterLink>
          </td>
          <td>{{ inv.client_name }}</td>
          <td>{{ formatDate(inv.issue_date) }}</td>
          <td>{{ formatDate(inv.due_date) }}</td>
          <td><StatusBadge :status="inv.status" /></td>
          <td class="num">{{ formatMoney(inv.total, inv.currency) }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.tabs button {
  border: none;
  background: none;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  padding: 0.5rem 0.75rem;
  color: var(--muted);
}

.tabs button.active {
  border-bottom-color: var(--primary);
  color: var(--text);
  font-weight: 600;
}
</style>
