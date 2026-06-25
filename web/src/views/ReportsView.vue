<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'

import { api, download } from '@/api/client'
import type { Amount, Client, RevenueReport, TimeReport } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import RevenueChart from '@/components/RevenueChart.vue'
import { formatDuration, formatMoney, isoDate } from '@/lib/format'

type Group = TimeReport['group_by']

const now = new Date()
const PRESETS = {
  'This month': [new Date(now.getFullYear(), now.getMonth(), 1), now],
  'Last month': [
    new Date(now.getFullYear(), now.getMonth() - 1, 1),
    new Date(now.getFullYear(), now.getMonth(), 0),
  ],
  'This year': [new Date(now.getFullYear(), 0, 1), now],
  'Last year': [new Date(now.getFullYear() - 1, 0, 1), new Date(now.getFullYear() - 1, 11, 31)],
} as const

const range = reactive({
  from: isoDate(PRESETS['This year'][0]),
  to: isoDate(PRESETS['This year'][1]),
})
const groupBy = ref<Group>('client')
const clientId = ref<number | ''>('')
const clients = ref<Client[]>([])
const report = ref<TimeReport | null>(null)
const error = ref('')
const year = ref(now.getFullYear())
const revenue = ref<RevenueReport | null>(null)
const revenueCurrency = ref('EUR')

const revenueCurrencies = () =>
  [...new Set((revenue.value?.invoiced ?? []).map((a) => a.currency))].sort()

async function loadRevenue() {
  revenue.value = await api.get<RevenueReport>('/reports/revenue', { year: year.value })
  const currencies = revenueCurrencies()
  if (currencies.length && !currencies.includes(revenueCurrency.value)) {
    revenueCurrency.value = currencies[0]!
  }
}

function preset(name: keyof typeof PRESETS) {
  range.from = isoDate(PRESETS[name][0])
  range.to = isoDate(PRESETS[name][1])
}

function amounts(list: Amount[]): string {
  return list.length ? list.map((a) => formatMoney(a.amount, a.currency)).join(' + ') : '—'
}

async function load() {
  error.value = ''
  try {
    report.value = await api.get<TimeReport>('/reports/time', query())
  } catch (e) {
    error.value = (e as Error).message
  }
}

function query() {
  return { from: range.from, to: range.to, group_by: groupBy.value, client_id: clientId.value }
}

async function exportCsv() {
  try {
    await download('/reports/time.csv', query(), `time-by-${groupBy.value}.csv`)
  } catch (e) {
    error.value = (e as Error).message
  }
}

watch([range, groupBy, clientId], load)
watch(year, loadRevenue)
onMounted(() => {
  api
    .get<Client[]>('/clients', { include_archived: true })
    .then((list) => (clients.value = list))
    .catch(() => {})
  load()
  loadRevenue().catch((e) => (error.value = (e as Error).message))
})
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Reports</h1>
    </div>

    <div class="controls card">
      <div class="presets">
        <button v-for="(_, name) in PRESETS" :key="name" type="button" @click="preset(name)">
          {{ name }}
        </button>
      </div>
      <input v-model="range.from" type="date" aria-label="From" />
      <input v-model="range.to" type="date" aria-label="To" />
      <select v-model="groupBy" aria-label="Group by">
        <option value="client">By client</option>
        <option value="project">By project</option>
        <option value="month">By month</option>
      </select>
      <select v-model="clientId" aria-label="Client">
        <option value="">All clients</option>
        <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <button type="button" :disabled="!report?.rows.length" @click="exportCsv">CSV</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <template v-else-if="report">
      <div class="totals">
        <div class="card stat">
          <span class="muted">Tracked</span>
          <strong>{{ formatDuration(report.tracked_seconds) }}</strong>
        </div>
        <div class="card stat">
          <span class="muted">Billable</span>
          <strong>{{ formatDuration(report.billable_seconds) }}</strong>
        </div>
        <div class="card stat">
          <span class="muted">Billable value</span>
          <strong>{{ amounts(report.amounts) }}</strong>
        </div>
      </div>

      <EmptyState v-if="!report.rows.length" title="Nothing tracked in this period" />
      <table v-else class="table">
        <thead>
          <tr>
            <th>
              {{ groupBy === 'month' ? 'Month' : groupBy === 'project' ? 'Project' : 'Client' }}
            </th>
            <th class="num">Tracked</th>
            <th class="num">Billable</th>
            <th class="num">Not invoiced</th>
            <th class="num">Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in report.rows" :key="row.key">
            <td>{{ row.label }}</td>
            <td class="num">{{ formatDuration(row.tracked_seconds) }}</td>
            <td class="num">{{ formatDuration(row.billable_seconds) }}</td>
            <td class="num">{{ formatDuration(row.unbilled_seconds) }}</td>
            <td class="num">{{ amounts(row.amounts) }}</td>
          </tr>
        </tbody>
      </table>
    </template>

    <div v-if="revenue" class="card revenue">
      <div class="revenue-header">
        <h2>Revenue {{ revenue.year }}</h2>
        <div class="header-actions">
          <select v-if="revenueCurrencies().length > 1" v-model="revenueCurrency">
            <option v-for="c in revenueCurrencies()" :key="c">{{ c }}</option>
          </select>
          <button type="button" aria-label="Previous year" @click="year--">‹</button>
          <button type="button" aria-label="Next year" @click="year++">›</button>
        </div>
      </div>
      <RevenueChart :report="revenue" :currency="revenueCurrency" />
      <p class="muted">
        Invoiced {{ amounts(revenue.invoiced) }} · Paid {{ amounts(revenue.paid) }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.presets {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  margin-right: auto;
}

.totals {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.revenue {
  margin-top: 1.5rem;
}

.revenue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.revenue-header h2 {
  font-size: 1.125rem;
  margin: 0;
}

.stat strong {
  font-size: 1.25rem;
}
</style>
