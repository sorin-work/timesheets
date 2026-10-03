<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api/client'
import type { InvoicesOverview, InvoiceStatus, InvoiceSummary } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonRows from '@/components/SkeletonRows.vue'
import { dueLabel, formatDate, formatMoney } from '@/lib/format'
import { useLoader } from '@/lib/useLoader'

const route = useRoute()
const router = useRouter()

const TABS: { value: InvoiceStatus | ''; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'draft', label: 'Drafts' },
  { value: 'sent', label: 'Sent' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'paid', label: 'Paid' },
]

const status = ref<InvoiceStatus | ''>((route.query.status as InvoiceStatus) ?? '')
const sort = ref<'number' | 'issue_date' | 'due_date' | 'total'>('number')
const order = ref<'asc' | 'desc'>('desc')
const {
  data: invoices,
  loading,
  error,
  load,
} = useLoader<InvoiceSummary[]>([], () =>
  api.get<InvoiceSummary[]>('/invoices', {
    status: status.value,
    sort: sort.value,
    order: order.value,
  }),
)

type SortKey = 'number' | 'issue_date' | 'due_date' | 'total'

function sortBy(key: SortKey) {
  if (sort.value === key) order.value = order.value === 'desc' ? 'asc' : 'desc'
  else {
    sort.value = key
    order.value = 'desc'
  }
  load()
}

function arrow(key: SortKey): string {
  return sort.value === key ? (order.value === 'desc' ? ' ↓' : ' ↑') : ''
}

const overview = ref<InvoicesOverview | null>(null)

function tabCount(value: InvoiceStatus | ''): number | null {
  if (!overview.value || value === '') return null
  return overview.value.statuses.find((s) => s.status === value)?.count ?? 0
}

function tabTotal(value: InvoiceStatus | ''): string {
  const entry = overview.value?.statuses.find((s) => s.status === value)
  return entry?.totals.map((t) => formatMoney(t.amount, t.currency)).join(' + ') ?? ''
}

watch(status, (value) => {
  router.replace({ query: value ? { status: value } : {} })
  load()
})

onMounted(() => {
  load()
  api
    .get<InvoicesOverview>('/invoices/overview')
    .then((o) => (overview.value = o))
    .catch(() => {})
})
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
        :title="tabTotal(tab.value)"
        @click="status = tab.value"
      >
        {{ tab.label }}
        <span v-if="tabCount(tab.value)" class="count">{{ tabCount(tab.value) }}</span>
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <SkeletonRows v-else-if="loading" />
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
          <th>
            <button class="sort" type="button" @click="sortBy('number')">
              Number{{ arrow('number') }}
            </button>
          </th>
          <th>Client</th>
          <th class="hide-sm">
            <button class="sort" type="button" @click="sortBy('issue_date')">
              Issued{{ arrow('issue_date') }}
            </button>
          </th>
          <th>
            <button class="sort" type="button" @click="sortBy('due_date')">
              Due{{ arrow('due_date') }}
            </button>
          </th>
          <th>Status</th>
          <th class="num">
            <button class="sort" type="button" @click="sortBy('total')">
              Total{{ arrow('total') }}
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="inv in invoices" :key="inv.id">
          <td>
            <RouterLink :to="`/invoices/${inv.id}`">{{ inv.number }}</RouterLink>
          </td>
          <td>{{ inv.client_name }}</td>
          <td class="hide-sm">{{ formatDate(inv.issue_date) }}</td>
          <td>
            {{ formatDate(inv.due_date) }}
            <small
              v-if="inv.status === 'sent' || inv.status === 'overdue'"
              :class="inv.status === 'overdue' ? 'error' : 'muted'"
            >
              · {{ dueLabel(inv.due_date) }}
            </small>
          </td>
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

.sort {
  border: none;
  background: none;
  padding: 0;
  font: inherit;
  text-transform: inherit;
  letter-spacing: inherit;
  color: inherit;
}

.count {
  font-size: 0.75rem;
  background: var(--subtle);
  border-radius: 999px;
  padding: 0 0.4rem;
  margin-left: 0.25rem;
}

.tabs button.active {
  border-bottom-color: var(--primary);
  color: var(--text);
  font-weight: 600;
}
</style>
