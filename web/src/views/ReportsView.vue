<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'

import { api } from '@/api/client'
import type { Amount, TimeReport } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
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
const report = ref<TimeReport | null>(null)
const error = ref('')

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
    report.value = await api.get<TimeReport>('/reports/time', {
      from: range.from,
      to: range.to,
      group_by: groupBy.value,
    })
  } catch (e) {
    error.value = (e as Error).message
  }
}

watch([range, groupBy], load)
onMounted(load)
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

.stat strong {
  font-size: 1.25rem;
}
</style>
