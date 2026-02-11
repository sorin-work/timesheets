<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api/client'
import type { Timesheet } from '@/api/types'
import { formatDuration, isoDate } from '@/lib/format'
import { addDays, dayLabel, mondayOf, weekLabel } from '@/lib/week'

const route = useRoute()
const router = useRouter()

const sheet = ref<Timesheet | null>(null)
const loading = ref(true)
const error = ref('')

const thisWeek = isoDate(mondayOf(new Date()))
const week = computed(() => (typeof route.query.week === 'string' ? route.query.week : thisWeek))
const today = isoDate(new Date())

async function load() {
  loading.value = true
  error.value = ''
  try {
    sheet.value = await api.get<Timesheet>('/timesheet', { week: week.value })
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function go(offset: number) {
  const target = offset === 0 ? thisWeek : addDays(sheet.value?.week_start ?? week.value, offset)
  router.push({ query: target === thisWeek ? {} : { week: target } })
}

watch(week, load)
onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Timesheet</h1>
      <div class="header-actions">
        <button type="button" aria-label="Previous week" @click="go(-7)">‹</button>
        <strong v-if="sheet">{{ weekLabel(sheet.week_start) }}</strong>
        <button type="button" aria-label="Next week" @click="go(7)">›</button>
        <button v-if="sheet?.week_start !== thisWeek" type="button" @click="go(0)">
          This week
        </button>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <div v-else-if="sheet" class="grid-wrap">
      <table class="table grid">
        <thead>
          <tr>
            <th>Project</th>
            <th v-for="day in sheet.days" :key="day" class="num" :class="{ today: day === today }">
              {{ dayLabel(day).weekday }}<br />
              <span class="muted">{{ dayLabel(day).day }}</span>
            </th>
            <th class="num">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!sheet.rows.length">
            <td :colspan="9" class="muted empty">No time logged this week.</td>
          </tr>
          <tr v-for="row in sheet.rows" :key="row.project_id">
            <td>
              <span class="dot" :style="{ background: row.color }" />
              {{ row.project_name }}
              <div class="muted small">{{ row.client_name }}</div>
            </td>
            <td v-for="(seconds, i) in row.seconds" :key="i" class="num">
              {{ seconds ? formatDuration(seconds) : '' }}
            </td>
            <td class="num strong">{{ formatDuration(row.total) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td>Total</td>
            <td v-for="(seconds, i) in sheet.totals" :key="i" class="num">
              {{ formatDuration(seconds) }}
            </td>
            <td class="num strong">{{ formatDuration(sheet.total) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>
    <p v-else-if="loading" class="muted">Loading…</p>
  </section>
</template>

<style scoped>
.grid-wrap {
  overflow-x: auto;
}

.grid th.today {
  color: var(--primary);
}

.grid tfoot td {
  font-weight: 600;
  background: #f1f5f9;
}

.strong {
  font-weight: 600;
}

.small {
  font-size: 0.75rem;
}

.empty {
  text-align: center;
  padding: 2rem;
}

.dot {
  display: inline-block;
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 999px;
  margin-right: 0.375rem;
}
</style>
