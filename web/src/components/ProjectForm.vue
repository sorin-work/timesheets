<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { api, ApiError } from '@/api/client'
import type { Client, Project } from '@/api/types'
import { formatMoney } from '@/lib/format'

const props = defineProps<{ project?: Project | null; clients: Client[] }>()
const emit = defineEmits<{ saved: [project: Project]; cancel: [] }>()

const COLORS = [
  '#4f46e5',
  '#0891b2',
  '#059669',
  '#ca8a04',
  '#dc2626',
  '#db2777',
  '#7c3aed',
  '#475569',
]

const form = reactive({
  client_id: props.project?.client_id ?? props.clients[0]?.id ?? 0,
  name: props.project?.name ?? '',
  hourly_rate: props.project?.hourly_rate ?? '',
  billable: props.project?.billable ?? true,
  color: props.project?.color ?? COLORS[0],
  budget_hours: props.project?.budget_hours ?? '',
})
const errors = ref<Record<string, string>>({})
const error = ref('')
const busy = ref(false)

const selectedClient = computed(() => props.clients.find((c) => c.id === form.client_id))
const ratePlaceholder = computed(() => {
  const c = selectedClient.value
  return c?.hourly_rate ? `Client rate: ${formatMoney(c.hourly_rate, c.currency)}` : 'No rate'
})

async function submit() {
  busy.value = true
  errors.value = {}
  error.value = ''
  const rate = String(form.hourly_rate).trim() || null
  const budget = String(form.budget_hours).trim() || null
  try {
    const saved = props.project
      ? await api.patch<Project>(`/projects/${props.project.id}`, {
          name: form.name,
          hourly_rate: rate,
          billable: form.billable,
          color: form.color,
          budget_hours: budget,
        })
      : await api.post<Project>('/projects', { ...form, hourly_rate: rate, budget_hours: budget })
    emit('saved', saved)
  } catch (e) {
    if (e instanceof ApiError) {
      errors.value = e.fieldErrors()
      error.value = e.message
    } else throw e
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <label>
      Client
      <select v-model.number="form.client_id" :disabled="!!project" required>
        <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </label>
    <label>
      Project name
      <input v-model="form.name" required maxlength="200" />
      <small v-if="errors.name" class="error">{{ errors.name }}</small>
    </label>
    <label>
      Hourly rate
      <input v-model="form.hourly_rate" inputmode="decimal" :placeholder="ratePlaceholder" />
      <small class="muted">Leave empty to use the client's rate.</small>
      <small v-if="errors.hourly_rate" class="error">{{ errors.hourly_rate }}</small>
    </label>
    <label>
      Budget (hours)
      <input v-model="form.budget_hours" inputmode="decimal" placeholder="No budget" />
      <small v-if="errors.budget_hours" class="error">{{ errors.budget_hours }}</small>
    </label>
    <label class="inline">
      <input v-model="form.billable" type="checkbox" />
      Time on this project is billable by default
    </label>
    <div>
      <span class="label">Colour</span>
      <div class="swatches">
        <button
          v-for="c in COLORS"
          :key="c"
          type="button"
          class="swatch"
          :class="{ selected: form.color === c }"
          :style="{ background: c }"
          :aria-label="c"
          @click="form.color = c"
        />
      </div>
    </div>
    <p v-if="error && !Object.keys(errors).length" class="error">{{ error }}</p>
    <div class="actions">
      <button type="button" @click="emit('cancel')">Cancel</button>
      <button class="primary" type="submit" :disabled="busy">
        {{ project ? 'Save changes' : 'Add project' }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.label {
  font-size: 0.875rem;
  font-weight: 500;
}

.swatches {
  display: flex;
  gap: 0.375rem;
  margin-top: 0.25rem;
}

.swatch {
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  border-radius: 999px;
  border: 2px solid transparent;
}

.swatch.selected {
  border-color: var(--text);
}
</style>
