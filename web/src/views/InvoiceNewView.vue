<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { api, ApiError } from '@/api/client'
import type { Client, Invoice, Settings, UnbilledSummary } from '@/api/types'
import TaxLinesEditor from '@/components/TaxLinesEditor.vue'
import { formatDuration, formatMoney, isoDate } from '@/lib/format'

const router = useRouter()

const today = new Date()
const firstOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
const lastOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0)

const clients = ref<Client[]>([])
const summary = ref<UnbilledSummary | null>(null)
const selected = ref<number[]>([])
const error = ref('')
const submitting = ref(false)

const form = reactive({
  client_id: 0,
  period_start: isoDate(firstOfLastMonth),
  period_end: isoDate(lastOfLastMonth),
  group_by: 'project' as 'project' | 'entry',
  due_days: '' as number | '',
  notes: '',
  taxes: [] as { name: string; rate: string }[],
})

const estimate = computed(() => {
  if (!summary.value) return 0
  return summary.value.projects
    .filter((p) => selected.value.includes(p.project_id))
    .reduce((sum, p) => sum + (p.billable_seconds / 3600) * Number(p.hourly_rate ?? 0), 0)
})

async function loadSummary() {
  summary.value = null
  if (!form.client_id || !form.period_start || !form.period_end) return
  try {
    summary.value = await api.get<UnbilledSummary>('/invoices/unbilled', {
      client_id: form.client_id,
      period_start: form.period_start,
      period_end: form.period_end,
    })
    selected.value = summary.value.projects.map((p) => p.project_id)
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function submit() {
  if (submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const invoice = await api.post<Invoice>('/invoices/generate', {
      ...form,
      due_days: form.due_days === '' ? null : form.due_days,
      notes: form.notes || null,
      project_ids: selected.value,
    })
    await router.push(`/invoices/${invoice.id}`)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'Could not create the invoice'
    submitting.value = false
  }
}

watch(() => [form.client_id, form.period_start, form.period_end], loadSummary)

onMounted(async () => {
  const [list, settings] = await Promise.all([
    api.get<Client[]>('/clients'),
    api.get<Settings>('/settings'),
  ])
  clients.value = list
  form.taxes = settings.default_taxes.map((t) => ({ ...t }))
  if (clients.value.length) form.client_id = clients.value[0]!.id
})
</script>

<template>
  <section class="new-invoice">
    <div class="page-header">
      <h1>New invoice</h1>
    </div>

    <form class="form card" @submit.prevent="submit">
      <label>
        Client
        <select v-model.number="form.client_id" required>
          <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </label>
      <div class="row">
        <label>
          From
          <input v-model="form.period_start" type="date" required />
        </label>
        <label>
          To
          <input v-model="form.period_end" type="date" required />
        </label>
      </div>

      <div v-if="summary">
        <p v-if="!summary.projects.length" class="muted">
          No unbilled billable time for this client in the period.
        </p>
        <table v-else class="table">
          <thead>
            <tr>
              <th></th>
              <th>Project</th>
              <th class="num">Entries</th>
              <th class="num">Hours</th>
              <th class="num">Rate</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in summary.projects" :key="p.project_id">
              <td>
                <input
                  v-model="selected"
                  type="checkbox"
                  :value="p.project_id"
                  :aria-label="p.project_name"
                />
              </td>
              <td>{{ p.project_name }}</td>
              <td class="num">{{ p.entries }}</td>
              <td class="num">
                {{ formatDuration(p.billable_seconds) }}
                <small v-if="p.billable_seconds !== p.seconds" class="muted">
                  ({{ formatDuration(p.seconds) }} tracked)
                </small>
              </td>
              <td class="num">
                <span v-if="p.hourly_rate">{{ formatMoney(p.hourly_rate, summary.currency) }}</span>
                <span v-else class="error">no rate</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="row">
        <label>
          Lines
          <select v-model="form.group_by">
            <option value="project">One line per project</option>
            <option value="entry">One line per time entry</option>
          </select>
        </label>
        <label>
          Payment due in (days)
          <input
            v-model.number="form.due_days"
            type="number"
            min="0"
            max="365"
            placeholder="From settings"
          />
        </label>
      </div>

      <TaxLinesEditor v-model="form.taxes" />

      <label>
        Notes
        <textarea v-model="form.notes" rows="3" placeholder="Payment details, thank you note…" />
      </label>

      <p v-if="summary?.projects.length" class="estimate">
        Estimated subtotal:
        <strong>{{ formatMoney(estimate, summary.currency) }}</strong>
      </p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div class="actions">
        <RouterLink class="button" to="/invoices">Cancel</RouterLink>
        <button class="primary" type="submit" :disabled="!selected.length || submitting">
          {{ submitting ? 'Creating…' : 'Create draft invoice' }}
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.new-invoice {
  max-width: 44rem;
}

.estimate {
  margin: 0;
}
</style>
