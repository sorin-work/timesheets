<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, download } from '@/api/client'
import type { Client, Entry, Page } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import EntryForm from '@/components/EntryForm.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import SkeletonRows from '@/components/SkeletonRows.vue'
import { groupByDay } from '@/lib/entries'
import { formatDate, formatDuration, formatTime } from '@/lib/format'
import { useProjects } from '@/stores/projects'
import { useTimer } from '@/stores/timer'
import { useToasts } from '@/stores/toasts'

const { projects, load: loadProjects } = useProjects()
const timer = useTimer()
const toast = useToasts()

const clients = ref<Client[]>([])
const page = ref<Page<Entry> | null>(null)
const loading = ref(true)
const error = ref('')
const currentPage = ref(1)
const editing = ref<Entry | null>(null)
const creating = ref(false)

function closeForm() {
  editing.value = null
  creating.value = false
}

function onSaved() {
  toast.success(editing.value ? 'Entry updated' : 'Time added')
  closeForm()
  load()
}

function onDeleted() {
  toast.success('Entry deleted')
  closeForm()
  load()
}

async function continueEntry(entry: Entry) {
  try {
    await timer.resume(entry.id)
    toast.info(`Timer started: ${entry.description || entry.project_name}`)
  } catch (e) {
    toast.error((e as Error).message)
  }
}

const selected = ref<Set<number>>(new Set())
const selectable = computed(() =>
  (page.value?.items ?? []).filter((e) => !e.running && !e.invoice_id).map((e) => e.id),
)
const allSelected = computed(
  () => selectable.value.length > 0 && selectable.value.every((id) => selected.value.has(id)),
)

function toggle(id: number) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
}

function toggleAll() {
  selected.value = allSelected.value ? new Set() : new Set(selectable.value)
}

async function bulk(action: 'billable' | 'non_billable' | 'delete') {
  const ids = [...selected.value]
  if (action === 'delete' && !confirm(`Delete ${ids.length} entries?`)) return
  try {
    const result = await api.post<{ updated: number; deleted: number }>('/entries/bulk', {
      ids,
      action,
    })
    toast.success(
      result.deleted ? `Deleted ${result.deleted} entries` : `Updated ${result.updated} entries`,
    )
    selected.value = new Set()
    await load()
  } catch (e) {
    toast.error((e as Error).message)
  }
}

const exporting = ref(false)

async function exportCsv() {
  exporting.value = true
  try {
    await download('/entries/export.csv', { ...filters }, 'time-entries.csv')
  } catch (e) {
    toast.error((e as Error).message)
  } finally {
    exporting.value = false
  }
}
const PAGE_SIZE = 25

const route = useRoute()
const router = useRouter()

function queryString(key: string): string {
  const value = route.query[key]
  return typeof value === 'string' ? value : ''
}

function queryNumber(key: string): number | '' {
  const value = Number(queryString(key))
  return Number.isInteger(value) && value > 0 ? value : ''
}

// Filters live in the URL so a filtered list can be bookmarked or shared.
const filters = reactive({
  client_id: queryNumber('client_id'),
  project_id: queryNumber('project_id'),
  from: queryString('from'),
  to: queryString('to'),
  billable: (['true', 'false'].includes(queryString('billable')) ? queryString('billable') : '') as
    '' | 'true' | 'false',
  q: queryString('q'),
})
currentPage.value = queryNumber('page') || 1

function syncUrl() {
  const query: Record<string, string> = {}
  for (const [key, value] of Object.entries(filters)) {
    if (value !== '') query[key] = String(value)
  }
  if (currentPage.value > 1) query.page = String(currentPage.value)
  router.replace({ query })
}

const projectOptions = computed(() =>
  filters.client_id === ''
    ? projects.value
    : projects.value.filter((p) => p.client_id === filters.client_id),
)

const days = computed(() => groupByDay(page.value?.items ?? []))

async function load() {
  loading.value = true
  error.value = ''
  try {
    page.value = await api.get<Page<Entry>>('/entries', {
      ...filters,
      page: currentPage.value,
      page_size: PAGE_SIZE,
    })
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, { client_id: '', project_id: '', from: '', to: '', billable: '', q: '' })
}

let debounce: ReturnType<typeof setTimeout> | undefined
watch(filters, () => {
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    currentPage.value = 1
    syncUrl()
    load()
  }, 250)
})

function goToPage(n: number) {
  currentPage.value = n
  syncUrl()
  load()
  window.scrollTo({ top: 0 })
}
watch(() => timer.state.version, load)

onMounted(async () => {
  loadProjects()
  clients.value = await api.get<Client[]>('/clients').catch(() => [])
  await load()
})
</script>

<template>
  <section>
    <div class="page-header">
      <h1>Time entries</h1>
      <div class="header-actions">
        <button type="button" :disabled="exporting || !page?.total" @click="exportCsv">
          Export CSV
        </button>
        <button class="primary" type="button" :disabled="!projects.length" @click="creating = true">
          Add time
        </button>
      </div>
    </div>

    <div class="filters card">
      <input v-model="filters.q" type="search" placeholder="Search descriptions" />
      <select v-model="filters.client_id" aria-label="Client">
        <option value="">All clients</option>
        <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="filters.project_id" aria-label="Project">
        <option value="">All projects</option>
        <option v-for="p in projectOptions" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <input v-model="filters.from" type="date" aria-label="From" />
      <input v-model="filters.to" type="date" aria-label="To" />
      <select v-model="filters.billable" aria-label="Billable">
        <option value="">Billable and not</option>
        <option value="true">Billable</option>
        <option value="false">Non-billable</option>
      </select>
      <button type="button" @click="resetFilters">Reset</button>
    </div>

    <div v-if="page?.items.length" class="bulk">
      <label class="inline">
        <input
          type="checkbox"
          :checked="allSelected"
          :disabled="!selectable.length"
          @change="toggleAll"
        />
        Select page
      </label>
      <template v-if="selected.size">
        <span class="muted">{{ selected.size }} selected</span>
        <button type="button" @click="bulk('billable')">Mark billable</button>
        <button type="button" @click="bulk('non_billable')">Mark non-billable</button>
        <button type="button" class="danger" @click="bulk('delete')">Delete</button>
      </template>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <SkeletonRows v-else-if="loading && !page" />
    <EmptyState
      v-else-if="page && !page.items.length"
      title="No time entries"
      message="Start the timer above or add time manually."
    />
    <div v-else class="days">
      <div v-for="group in days" :key="group.day" class="day">
        <div class="day-header">
          <strong>{{ formatDate(group.day) }}</strong>
          <span class="muted">{{ formatDuration(group.total) }}</span>
        </div>
        <table class="table">
          <tbody>
            <tr
              v-for="e in group.entries"
              :key="e.id"
              class="clickable"
              @click="e.running ? null : (editing = e)"
            >
              <td class="check" @click.stop>
                <input
                  type="checkbox"
                  :checked="selected.has(e.id)"
                  :disabled="e.running || !!e.invoice_id"
                  :aria-label="`Select ${e.description || e.project_name}`"
                  @change="toggle(e.id)"
                />
              </td>
              <td class="desc">
                <div>{{ e.description || '(no description)' }}</div>
                <small class="muted">{{ e.client_name }} · {{ e.project_name }}</small>
              </td>
              <td>
                <span v-if="!e.billable" class="badge">non-billable</span>
                <span v-if="e.invoice_id" class="badge billed">invoiced</span>
              </td>
              <td class="muted times hide-sm">
                {{ formatTime(e.started_at) }} –
                {{ e.ended_at ? formatTime(e.ended_at) : 'now' }}
              </td>
              <td class="num">{{ e.running ? 'running' : formatDuration(e.duration_seconds) }}</td>
              <td class="row-actions">
                <button
                  v-if="!e.running"
                  type="button"
                  class="play"
                  title="Continue this task"
                  aria-label="Continue this task"
                  @click.stop="continueEntry(e)"
                >
                  ▶
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <PaginationBar
        v-if="page && page.total > PAGE_SIZE"
        :page="page.page"
        :pages="page.pages"
        :total="page.total"
        @change="goToPage"
      />
    </div>

    <ModalDialog
      v-if="creating || editing"
      :title="editing ? 'Edit entry' : 'Add time'"
      @close="closeForm"
    >
      <EntryForm :entry="editing" @saved="onSaved" @deleted="onDeleted" @cancel="closeForm" />
    </ModalDialog>
  </section>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  padding: 0.75rem;
}

.filters input[type='search'] {
  flex: 1;
  min-width: 12rem;
}

.days {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.day-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.375rem;
}

.desc {
  width: 55%;
}

.bulk {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  min-height: 2.25rem;
}

.check {
  width: 2rem;
}

.play {
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
}

.clickable {
  cursor: pointer;
}

.clickable:hover td {
  background: var(--hover);
}

.times {
  white-space: nowrap;
}

.badge.billed {
  background: #dcfce7;
  color: #166534;
}
</style>
