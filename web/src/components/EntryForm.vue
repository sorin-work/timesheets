<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'
import type { Entry } from '@/api/types'
import { formatDuration, isoDate } from '@/lib/format'
import { useProjects } from '@/stores/projects'

const props = defineProps<{ entry?: Entry | null; defaultDate?: string }>()
const emit = defineEmits<{ saved: [entry: Entry]; deleted: []; cancel: [] }>()

const { projects } = useProjects()

function timeOf(value: string): string {
  const d = new Date(value)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const initial = {
  project_id: props.entry?.project_id ?? projects.value[0]?.id ?? 0,
  date: props.entry
    ? isoDate(new Date(props.entry.started_at))
    : (props.defaultDate ?? isoDate(new Date())),
  start: props.entry ? timeOf(props.entry.started_at) : '09:00',
  end: props.entry?.ended_at ? timeOf(props.entry.ended_at) : '10:00',
  description: props.entry?.description ?? '',
  billable: props.entry?.billable ?? true,
}
const form = reactive({ ...initial })
const error = ref('')
const busy = ref(false)
const locked = computed(() => !!props.entry?.invoice_id)

function toInstant(date: string, time: string): Date {
  return new Date(`${date}T${time}:00`)
}

const range = computed(() => {
  const start = toInstant(form.date, form.start)
  let end = toInstant(form.date, form.end)
  // "22:00 - 01:00" means the entry runs past midnight.
  if (end <= start) end = new Date(end.getTime() + 24 * 3600 * 1000)
  return { start, end }
})

const duration = computed(() => (range.value.end.getTime() - range.value.start.getTime()) / 1000)

function changedFields(): Record<string, unknown> {
  const changes: Record<string, unknown> = {}
  if (form.project_id !== initial.project_id) changes.project_id = form.project_id
  if (form.date !== initial.date || form.start !== initial.start)
    changes.started_at = range.value.start.toISOString()
  if (form.date !== initial.date || form.end !== initial.end)
    changes.ended_at = toInstant(form.date, form.end).toISOString()
  if (form.description !== initial.description) changes.description = form.description
  if (form.billable !== initial.billable) changes.billable = form.billable
  return changes
}

async function submit() {
  busy.value = true
  error.value = ''
  try {
    let saved: Entry
    if (props.entry) {
      saved = await api.patch<Entry>(`/entries/${props.entry.id}`, changedFields())
    } else {
      saved = await api.post<Entry>('/entries', {
        project_id: form.project_id,
        started_at: range.value.start.toISOString(),
        ended_at: range.value.end.toISOString(),
        description: form.description,
        billable: form.billable,
      })
    }
    emit('saved', saved)
  } catch (e) {
    if (e instanceof ApiError) error.value = e.details[0]?.message ?? e.message
    else throw e
  } finally {
    busy.value = false
  }
}

async function remove() {
  if (!props.entry || !confirm('Delete this entry?')) return
  busy.value = true
  try {
    await api.delete(`/entries/${props.entry.id}`)
    emit('deleted')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <p v-if="locked" class="notice">
      This entry is on an invoice and can't be changed. Delete the draft invoice to edit it.
    </p>
    <fieldset :disabled="locked" class="form">
      <label>
        Project
        <select v-model.number="form.project_id" required>
          <option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.client_name }} · {{ p.name }}
          </option>
        </select>
      </label>
      <label>
        Description
        <input v-model="form.description" maxlength="500" placeholder="What did you do?" />
      </label>
      <div class="row three">
        <label>
          Date
          <input v-model="form.date" type="date" required />
        </label>
        <label>
          From
          <input v-model="form.start" type="time" required />
        </label>
        <label>
          To
          <input v-model="form.end" type="time" required />
        </label>
      </div>
      <p class="muted">Duration: {{ formatDuration(duration) }}</p>
      <label class="inline">
        <input v-model="form.billable" type="checkbox" />
        Billable
      </label>
    </fieldset>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="actions">
      <button v-if="entry && !locked" type="button" class="danger" @click="remove">Delete</button>
      <span class="spacer" />
      <button type="button" @click="emit('cancel')">Cancel</button>
      <button v-if="!locked" class="primary" type="submit" :disabled="busy">
        {{ entry ? 'Save' : 'Add entry' }}
      </button>
    </div>
  </form>
</template>

<style scoped>
fieldset {
  border: none;
  padding: 0;
  margin: 0;
}

.row.three {
  grid-template-columns: 1.4fr 1fr 1fr;
}

.spacer {
  flex: 1;
}

.notice {
  background: #fef3c7;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  margin: 0;
}
</style>
