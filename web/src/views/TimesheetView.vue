<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api/client'
import type { Settings, Timesheet, TimesheetRow } from '@/api/types'
import GridCell from '@/components/GridCell.vue'
import { formatDuration, isoDate } from '@/lib/format'
import { addDays, dayLabel, mondayOf, weekLabel } from '@/lib/week'
import { useProjects } from '@/stores/projects'

const { projects, load: loadProjects } = useProjects()

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

const saving = ref(false)
const target = ref<number | null>(null)
const progress = computed(() =>
  target.value && sheet.value
    ? Math.min(100, Math.round((sheet.value.total / 3600 / target.value) * 100))
    : null,
)
const extra = ref<number[]>([])
const adding = ref<number | ''>('')

const rows = computed<TimesheetRow[]>(() => {
  const existing = sheet.value?.rows ?? []
  const shown = new Set(existing.map((r) => r.project_id))
  const added = extra.value
    .filter((id) => !shown.has(id))
    .map((id) => projects.value.find((p) => p.id === id))
    .filter((p) => p !== undefined)
    .map((p) => ({
      project_id: p.id,
      project_name: p.name,
      client_name: p.client_name,
      color: p.color,
      seconds: [0, 0, 0, 0, 0, 0, 0],
      total: 0,
    }))
  return [...existing, ...added]
})

const addable = computed(() => {
  const shown = new Set(rows.value.map((r) => r.project_id))
  return projects.value.filter((p) => !shown.has(p.id))
})

async function copyLastWeek() {
  if (!sheet.value) return
  try {
    const previous = await api.get<Timesheet>('/timesheet', {
      week: addDays(sheet.value.week_start, -7),
    })
    const ids = previous.rows.map((r) => r.project_id)
    if (!ids.length) {
      error.value = 'Nothing was logged last week'
      return
    }
    extra.value = [...new Set([...extra.value, ...ids])]
  } catch (e) {
    error.value = (e as Error).message
  }
}

function addRow() {
  if (adding.value !== '') extra.value.push(adding.value)
  adding.value = ''
}

async function setCell(projectId: number, date: string, minutes: number) {
  saving.value = true
  error.value = ''
  try {
    sheet.value = await api.put<Timesheet>('/timesheet/cell', {
      project_id: projectId,
      date,
      minutes,
    })
  } catch (e) {
    error.value = (e as Error).message
    await load()
  } finally {
    saving.value = false
  }
}

function go(offset: number) {
  const target = offset === 0 ? thisWeek : addDays(sheet.value?.week_start ?? week.value, offset)
  router.push({ query: target === thisWeek ? {} : { week: target } })
}

watch(week, () => {
  extra.value = []
  load()
})
onMounted(() => {
  loadProjects()
  api
    .get<Settings>('/settings')
    .then((s) => (target.value = s.weekly_target_hours ? Number(s.weekly_target_hours) : null))
    .catch(() => {})
  load()
})
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

    <div v-if="progress !== null && sheet" class="target" :title="`${progress}% of ${target} h`">
      <div class="track"><div class="fill" :style="{ width: `${progress}%` }" /></div>
      <span class="muted">{{ formatDuration(sheet.total) }} of {{ target }} h this week</span>
    </div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <div v-if="sheet" class="grid-wrap">
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
          <tr v-if="!rows.length">
            <td :colspan="9" class="muted empty">
              No time logged this week. Add a project below to fill in hours.
            </td>
          </tr>
          <tr v-for="row in rows" :key="row.project_id">
            <td>
              <span class="dot" :style="{ background: row.color }" />
              {{ row.project_name }}
              <div class="muted small">{{ row.client_name }}</div>
            </td>
            <td v-for="(seconds, i) in row.seconds" :key="i" class="num cell-td">
              <GridCell
                :seconds="seconds"
                :label="`${row.project_name}, ${sheet.days[i]}`"
                @change="(minutes) => setCell(row.project_id, sheet!.days[i]!, minutes)"
              />
            </td>
            <td class="num strong">{{ formatDuration(row.total) }}</td>
          </tr>
        </tbody>
        <tbody>
          <tr class="add-row">
            <td colspan="9">
              <button v-if="!rows.length" type="button" class="copy" @click="copyLastWeek">
                Copy projects from last week
              </button>
              <select v-model="adding" aria-label="Add project" @change="addRow">
                <option value="">+ Add project row…</option>
                <option v-for="p in addable" :key="p.id" :value="p.id">
                  {{ p.client_name }} · {{ p.name }}
                </option>
              </select>
            </td>
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

.target {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.track {
  flex: 1;
  max-width: 24rem;
  height: 0.5rem;
  border-radius: 999px;
  background: var(--subtle);
  overflow: hidden;
}

.fill {
  height: 100%;
  background: var(--primary);
}

.cell-td:focus-within {
  background: var(--hover);
}

.cell-td {
  padding: 0.125rem 0.25rem !important;
}

.grid th.today {
  color: var(--primary);
}

.copy {
  margin-right: 0.5rem;
}

.add-row select {
  border-style: dashed;
}

.grid tfoot td {
  font-weight: 600;
  background: var(--subtle);
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
